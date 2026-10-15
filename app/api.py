import json
import os
from datetime import date
from typing import Literal, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.assistant import (
    get_pending_action,
    remove_pending_action,
    run_assistant_chat,
)
from app.database import engine
from app.prompts import build_improved_prompt


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="Dress Rental Planner API"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "https://the-muse-edit.onrender.com",
        "https://themuse.space",
        "https://www.themuse.space",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    amount: float = Field(gt=0)
    category: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str = Field(min_length=1)
    date: Optional[date] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: Optional[str] = None


@app.get("/api/transactions")
async def get_transactions(
    transaction_type: Literal[
        "all",
        "income",
        "expense",
    ] = Query(default="all")
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
