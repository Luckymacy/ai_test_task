from datetime import date
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import engine


app = FastAPI(title="Dress Rental Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    date: Optional[date] = None


@app.get("/api/transactions")
async def get_transactions(
    transaction_type: Literal["all", "income", "expense"] = Query(default="all")
):
    async with engine.connect() as connection:
        if transaction_type == "all":
            result = await connection.execute(
                text(
                    """
                    SELECT
                        t.id,
                        t.order_id,
                        t.date,
                        t.type,
                        t.amount,
                        t.category,
                        t.description,
                        o.client_name
                    FROM transactions t
                    LEFT JOIN orders o ON o.id = t.order_id
                    ORDER BY t.created_at DESC
                    """
                )
            )
        else:
            result = await connection.execute(
                text(
                    """
                    SELECT
                        t.id,
                        t.order_id,
                        t.date,
                        t.type,
                        t.amount,
                        t.category,
                        t.description,
                        o.client_name
                    FROM transactions t
                    LEFT JOIN orders o ON o.id = t.order_id
                    WHERE t.type = :transaction_type
                    ORDER BY t.created_at DESC
                    """
                ),
                {"transaction_type": transaction_type},
            )

        transactions = [dict(row._mapping) for row in result]

    return transactions


@app.post("/api/transactions")
async def create_transaction(transaction: TransactionCreate):
    transaction_date = transaction.date or date.today()

    async with engine.begin() as connection:
        result = await connection.execute(
            text(
                """
                INSERT INTO transactions (
                    date,
                    type,
                    amount,
                    category,
                    description
                )
                VALUES (
                    :date,
                    :type,
                    :amount,
                    :category,
                    :description
                )
                RETURNING
                    id,
                    order_id,
                    date,
                    type,
                    amount,
                    category,
                    description
                """
            ),
            {
                "date": transaction_date,
                "type": transaction.type,
                "amount": transaction.amount,
                "category": transaction.category,
                "description": transaction.description,
            },
        )

        created_transaction = dict(result.mappings().one())

    return created_transaction


@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int):
    async with engine.begin() as connection:
        result = await connection.execute(
            text(
                """
                DELETE FROM transactions
                WHERE id = :transaction_id
                RETURNING id
                """
            ),
            {"transaction_id": transaction_id},
        )

        deleted_id = result.scalar_one_or_none()

    if deleted_id is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return {
        "message": "Transaction deleted",
        "id": deleted_id,
    }


@app.get("/api/summary")
async def get_summary():
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT
                    COALESCE(
                        SUM(
                            CASE
                                WHEN type = 'income'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN type = 'expense'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS expenses
                FROM transactions
                """
            )
        )

        row = result.mappings().one()

        income = row["income"]
        expenses = row["expenses"]

    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
    }