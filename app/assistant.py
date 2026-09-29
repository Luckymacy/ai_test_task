import json
import logging
from collections import defaultdict
from typing import Dict, List

from openai import AsyncOpenAI
from sqlalchemy import text

from app.database import engine


logger = logging.getLogger("uvicorn.error")

THREAD_MEMORY: Dict[str, List[dict]] = defaultdict(list)
MAX_MEMORY_MESSAGES = 10


TOOLS = [
    {
        "type": "function",
        "name": "get_planned_shipments",
        "description": (
            "Отримати активні бронювання студії The Muse Edit, "
            "які ще потрібно відправити клієнтам. "
            "Використовуй цей tool, коли користувач питає "
            "про заплановані або майбутні відправки."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_expected_returns",
        "description": (
            "Отримати бронювання студії The Muse Edit, "
            "які вже відправлені клієнтам і від яких "
            "очікується повернення."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_financial_summary",
        "description": (
            "Отримати актуальні загальні доходи, витрати "
            "та баланс студії The Muse Edit."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


async def get_planned_shipments():
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT
                    id,
                    client_name,
                    status,
                    rental_status,
                    planned_shipping_date,
                    expected_return_date
                FROM orders
                WHERE rental_status = 'booked'
                  AND planned_shipping_date IS NOT NULL
                ORDER BY planned_shipping_date ASC
                """
            )
        )

        rows = result.mappings().all()

    return [
        {
            "order_id": row["id"],
            "client_name": row["client_name"],
            "payment_status": row["status"],
            "rental_status": row["rental_status"],
            "planned_shipping_date": str(
                row["planned_shipping_date"]
            ),
            "expected_return_date": (
                str(row["expected_return_date"])
                if row["expected_return_date"]
                else None
            ),
        }
        for row in rows
    ]


async def get_expected_returns():
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT
                    id,
                    client_name,
                    status,
                    rental_status,
                    planned_shipping_date,
                    expected_return_date
                FROM orders
                WHERE rental_status = 'shipped'
                  AND expected_return_date IS NOT NULL
                ORDER BY expected_return_date ASC
                """
            )
        )

        rows = result.mappings().all()

    return [
        {
            "order_id": row["id"],
            "client_name": row["client_name"],
            "payment_status": row["status"],
            "rental_status": row["rental_status"],
            "planned_shipping_date": (
                str(row["planned_shipping_date"])
                if row["planned_shipping_date"]
                else None
            ),
            "expected_return_date": str(
                row["expected_return_date"]
            ),
        }
        for row in rows
    ]


async def get_financial_summary():
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

    income = float(row["income"])
    expenses = float(row["expenses"])

    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
    }


async def execute_tool(name: str, arguments: dict):
    logger.info(
        "AI tool call: name=%s arguments=%s",
        name,
        arguments,
    )

    if name == "get_planned_shipments":
        result = await get_planned_shipments()

    elif name == "get_expected_returns":
        result = await get_expected_returns()

    elif name == "get_financial_summary":
        result = await get_financial_summary()

    else:
        raise ValueError(f"Unknown tool: {name}")

    logger.info(
        "AI tool result: name=%s result=%s",
        name,
        result,
    )

    return result


def get_thread_memory(thread_id: str):
    return THREAD_MEMORY[thread_id]


def add_to_memory(
    thread_id: str,
    role: str,
    content: str,
):
    memory = THREAD_MEMORY[thread_id]

    memory.append(
        {
            "role": role,
            "content": content,
        }
    )

    if len(memory) > MAX_MEMORY_MESSAGES:
        THREAD_MEMORY[thread_id] = memory[
            -MAX_MEMORY_MESSAGES:
        ]


async def run_assistant_chat(
    client: AsyncOpenAI,
    thread_id: str,
    message: str,
):
    memory = get_thread_memory(thread_id)

    input_messages = [
        {
            "role": "system",
            "content": (
                "Ти AI-помічник студії оренди одягу "
                "The Muse Edit. "
                "Твоя задача — допомагати власниці студії "
                "контролювати бронювання, відправки, "
                "повернення та фінанси. "
                "Якщо користувач питає, які бронювання "
                "потрібно відправити, які відправки "
                "заплановані або що треба відправити "
                "найближчим часом, використовуй "
                "get_planned_shipments. "
                "Якщо користувач питає, які бронювання "
                "очікуємо назад, хто має повернути речі "
                "або які повернення заплановані, "
                "використовуй get_expected_returns. "
                "Якщо користувач питає про доходи, "
                "витрати або баланс, використовуй "
                "get_financial_summary. "
                "Усі tools є read-only. "
                "Ніколи не змінюй дані в базі. "
                "Не вигадуй клієнтів, дати, суми, "
                "бронювання або статуси. "
                "Якщо tool повернув порожній список, "
                "прямо скажи, що відповідних бронювань "
                "зараз немає. "
                "Відповідай українською мовою, "
                "коротко та зрозуміло."
            ),
        }
    ]

    input_messages.extend(memory)

    input_messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    response = await client.responses.create(
        model="gpt-5.6-luna",
        input=input_messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    tool_outputs = []

    for item in response.output:
        if item.type != "function_call":
            continue

        arguments = json.loads(
            item.arguments or "{}"
        )

        result = await execute_tool(
            name=item.name,
            arguments=arguments,
        )

        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(
                    result,
                    ensure_ascii=False,
                ),
            }
        )

    if tool_outputs:
        response = await client.responses.create(
            model="gpt-5.6-luna",
            previous_response_id=response.id,
            input=tool_outputs,
            tools=TOOLS,
        )

    answer = response.output_text.strip()

    add_to_memory(
        thread_id=thread_id,
        role="user",
        content=message,
    )

    add_to_memory(
        thread_id=thread_id,
        role="assistant",
        content=answer,
    )

    return {
        "thread_id": thread_id,
        "answer": answer,
        "memory_size": len(
            get_thread_memory(thread_id)
        ),
    }