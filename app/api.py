from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine


app = FastAPI(title="Dress Rental Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/transactions")
async def get_transactions():
    async with engine.connect() as connection:
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

        transactions = [
            dict(row._mapping)
            for row in result
        ]

    return transactions


@app.get("/api/summary")
async def get_summary():
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT
                    COALESCE(
                        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END),
                        0
                    ) AS income,
                    COALESCE(
                        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END),
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