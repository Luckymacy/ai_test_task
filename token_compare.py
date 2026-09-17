import json
import tiktoken


transactions = [
    {
        "type": "income",
        "amount": 1800,
        "category": "rental",
        "description": "Оренда сукні",
    },
    {
        "type": "income",
        "amount": 1600,
        "category": "rental",
        "description": "Оренда костюма",
    },
    {
        "type": "expense",
        "amount": 200,
        "category": "cleaning",
        "description": "Хімчистка",
    },
]


summary = {
    "total_income": 3400,
    "total_expenses": 200,
    "balance": 3200,
    "expense_categories": {
        "cleaning": 200,
    },
}


raw_json = json.dumps(
    transactions,
    ensure_ascii=False,
    indent=2,
)

summary_json = json.dumps(
    summary,
    ensure_ascii=False,
    indent=2,
)


encoding = tiktoken.get_encoding("o200k_base")


raw_tokens = len(
    encoding.encode(raw_json)
)

summary_tokens = len(
    encoding.encode(summary_json)
)


print("RAW JSON tokens:", raw_tokens)
print("SUMMARY tokens:", summary_tokens)

difference = raw_tokens - summary_tokens

print("Token difference:", difference)

if raw_tokens > 0:
    saving_percent = (
        difference / raw_tokens
    ) * 100

    print(
        "Token saving:",
        round(saving_percent, 1),
        "%"
    )