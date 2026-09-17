import os
from datetime import date
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import engine
from app.prompts import build_improved_prompt


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


app = FastAPI(title="Dress Rental Planner API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
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
    transaction_type: Literal["all", "income", "expense"] = Query(
        default="all"
    )
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
                    LEFT JOIN orders o
                        ON o.id = t.order_id
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
                    LEFT JOIN orders o
                        ON o.id = t.order_id
                    WHERE t.type = :transaction_type
                    ORDER BY t.created_at DESC
                    """
                ),
                {
                    "transaction_type": transaction_type,
                },
            )

        transactions = [
            dict(row._mapping)
            for row in result
        ]

    return transactions


@app.post("/api/transactions")
async def create_transaction(
    transaction: TransactionCreate
):
    transaction_date = (
        transaction.date or date.today()
    )

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

        created_transaction = dict(
            result.mappings().one()
        )

    return created_transaction


@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: int
):
    async with engine.begin() as connection:
        result = await connection.execute(
            text(
                """
                DELETE FROM transactions
                WHERE id = :transaction_id
                RETURNING id
                """
            ),
            {
                "transaction_id": transaction_id,
            },
        )

        deleted_id = result.scalar_one_or_none()

    if deleted_id is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
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


@app.post("/api/ai/analyze-transactions")
async def analyze_transactions():
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set",
        )

    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT
                    date,
                    type,
                    amount,
                    category,
                    description
                FROM transactions
                ORDER BY created_at DESC
                LIMIT 50
                """
            )
        )

        rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No transactions to analyze",
        )

    transactions = []

    for row in rows:
        transactions.append(
            {
                "date": str(row["date"]),
                "type": row["type"],
                "amount": float(row["amount"]),
                "category": row["category"],
                "description": row["description"],
            }
        )

    prompt = build_improved_prompt(transactions)

    try:
        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY
        )

        response = await client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
        )

        ai_text = response.output_text.strip()

        import json
        analysis = json.loads(ai_text)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned invalid JSON",
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(error)}",
        )

    required_fields = [
        "summary",
        "top_expense_categories",
        "risks",
        "advice",
    ]

    for field in required_fields:
        if field not in analysis:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"AI response is missing "
                    f"field: {field}"
                ),
            )

    return analysis