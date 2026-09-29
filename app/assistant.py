import json
import logging
from collections import defaultdict
from typing import Dict, List
from uuid import uuid4

from openai import AsyncOpenAI
from sqlalchemy import text

from app.database import engine


logger = logging.getLogger("uvicorn.error")

THREAD_MEMORY: Dict[str, List[dict]] = defaultdict(list)
MAX_MEMORY_MESSAGES = 10

PENDING_ACTIONS: Dict[str, dict] = {}


TOOLS = [
    {
        "type": "function",
        "name": "get_planned_shipments",
        "description": (
            "Отримати активні бронювання студії The Muse Edit, "
            "які ще потрібно відправити клієнтам."
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
    {
        "type": "function",
        "name": "mark_order_shipped",
        "description": (
            "Запропонувати позначити бронювання як відправлене. "
            "Ця дія НЕ повинна виконуватися одразу. "
            "Вона лише створює pending action для підтвердження користувачем."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "ID бронювання",
                }
            },
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "mark_order_returned",
        "description": (
            "Запропонувати позначити бронювання як повернене. "
            "Ця дія НЕ повинна виконуватися одразу. "
            "Вона лише створює pending action для підтвердження користувачем."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "ID бронювання",
                }
            },
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


ACTION_TOOL_NAMES = {
    "mark_order_shipped",
    "mark_order_returned",
}


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


async def get_order(order_id: int):
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
                WHERE id = :order_id
                """
            ),
            {"order_id": order_id},
        )

        row = result.mappings().one_or_none()

    if row is None:
        return None

    return {
        "order_id": row["id"],
        "client_name": row["client_name"],
        "payment_status": row["status"],
        "rental_status": row["rental_status"],
        "planned_shipping_date": (
            str(row["planned_shipping_date"])
            if row["planned_shipping_date"]
            else None
        ),
        "expected_return_date": (
            str(row["expected_return_date"])
            if row["expected_return_date"]
            else None
        ),
    }


async def create_pending_action(
    thread_id: str,
    action_type: str,
    order_id: int,
):
    order = await get_order(order_id)

    if order is None:
        return {
            "success": False,
            "message": (
                f"Бронювання №{order_id} не знайдено."
            ),
        }, None

    if (
        action_type == "mark_order_shipped"
        and order["rental_status"] != "booked"
    ):
        return {
            "success": False,
            "message": (
                f"Бронювання №{order_id} має статус "
                f"{order['rental_status']} і не може бути "
                "позначене як відправлене."
            ),
        }, None

    if (
        action_type == "mark_order_returned"
        and order["rental_status"] != "shipped"
    ):
        return {
            "success": False,
            "message": (
                f"Бронювання №{order_id} має статус "
                f"{order['rental_status']} і не може бути "
                "позначене як повернене."
            ),
        }, None

    action_id = str(uuid4())

    if action_type == "mark_order_shipped":
        title = "Позначити бронювання як відправлене"
        target_status = "shipped"
    else:
        title = "Позначити бронювання як повернене"
        target_status = "returned"

    pending_action = {
        "action_id": action_id,
        "thread_id": thread_id,
        "action_type": action_type,
        "order_id": order_id,
        "client_name": order["client_name"],
        "current_status": order["rental_status"],
        "target_status": target_status,
        "title": title,
        "status": "pending",
    }

    PENDING_ACTIONS[action_id] = pending_action

    logger.info(
        "AI pending action created: %s",
        pending_action,
    )

    return {
        "success": True,
        "requires_confirmation": True,
        "action_id": action_id,
        "message": (
            f"Дію підготовлено. Потрібне підтвердження "
            f"для бронювання №{order_id}."
        ),
    }, pending_action


async def execute_tool(
    name: str,
    arguments: dict,
    thread_id: str,
):
    logger.info(
        "AI tool call: name=%s arguments=%s",
        name,
        arguments,
    )

    pending_action = None

    if name == "get_planned_shipments":
        result = await get_planned_shipments()

    elif name == "get_expected_returns":
        result = await get_expected_returns()

    elif name == "get_financial_summary":
        result = await get_financial_summary()

    elif name == "mark_order_shipped":
        result, pending_action = (
            await create_pending_action(
                thread_id=thread_id,
                action_type=name,
                order_id=arguments["order_id"],
            )
        )

    elif name == "mark_order_returned":
        result, pending_action = (
            await create_pending_action(
                thread_id=thread_id,
                action_type=name,
                order_id=arguments["order_id"],
            )
        )

    else:
        raise ValueError(f"Unknown tool: {name}")

    logger.info(
        "AI tool result: name=%s result=%s",
        name,
        result,
    )

    return result, pending_action


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


def get_pending_action(action_id: str):
    return PENDING_ACTIONS.get(action_id)


def remove_pending_action(action_id: str):
    return PENDING_ACTIONS.pop(action_id, None)


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
                "Допомагай власниці контролювати "
                "бронювання, відправки, повернення "
                "та фінанси. "
                "Для читання актуальних даних використовуй "
                "read-only tools. "
                "Якщо користувач просить позначити "
                "бронювання як відправлене, використовуй "
                "mark_order_shipped. "
                "Якщо користувач просить позначити "
                "бронювання як повернене, використовуй "
                "mark_order_returned. "
                "Action tools ніколи не змінюють базу "
                "безпосередньо. Вони лише створюють "
                "pending action для підтвердження. "
                "Після створення pending action прямо скажи, "
                "що дія очікує підтвердження користувача. "
                "Не стверджуй, що статус уже змінено. "
                "Не вигадуй клієнтів, дати, суми, "
                "бронювання або статуси. "
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
    pending_action = None

    for item in response.output:
        if item.type != "function_call":
            continue

        arguments = json.loads(
            item.arguments or "{}"
        )

        if (
            item.name in ACTION_TOOL_NAMES
            and pending_action is not None
        ):
            result = {
                "success": False,
                "message": (
                    "За один запит можна підготувати "
                    "лише одну контрольовану дію."
                ),
            }
            current_pending_action = None

        else:
            result, current_pending_action = (
                await execute_tool(
                    name=item.name,
                    arguments=arguments,
                    thread_id=thread_id,
                )
            )

        if current_pending_action:
            pending_action = current_pending_action

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
        "pending_action": pending_action,
    }