import json


WEAK_PROMPT_TEMPLATE = """
Проаналізуй фінансові операції студії оренди одягу.

Операції:
{transactions_json}

Поверни короткий аналіз:
- підсумок;
- основні категорії витрат;
- ризики;
- рекомендації.
"""


IMPROVED_PROMPT_TEMPLATE = """
Ти фінансовий AI-аналітик невеликої студії оренди одягу The Muse Edit.

Проаналізуй тільки наведені фінансові операції.
Не вигадуй дані, яких немає у вхідних даних.

Операції:
{transactions_json}

Поверни ТІЛЬКИ валідний JSON.
Не використовуй Markdown.
Не додавай жодного тексту до або після JSON.

Структура відповіді повинна бути строго такою:

{{
  "summary": "короткий підсумок фінансової ситуації",
  "top_expense_categories": [
    "категорія 1",
    "категорія 2"
  ],
  "risks": [
    "ризик 1",
    "ризик 2"
  ],
  "advice": [
    "порада 1",
    "порада 2"
  ]
}}

Правила:
- відповідь українською мовою;
- summary має бути коротким і базуватися тільки на даних;
- top_expense_categories має містити тільки реальні категорії витрат;
- risks мають бути сформульовані як можливі ризики, а не як факти без доказів;
- advice має містити практичні рекомендації для студії;
- не дублюй однакові рекомендації;
- якщо даних недостатньо, прямо вкажи це в аналізі;
- не вигадуй клієнтів, суми, категорії або причини витрат.
"""


def transactions_to_json(transactions):
    return json.dumps(
        transactions,
        ensure_ascii=False,
        indent=2,
    )


def build_weak_prompt(transactions):
    transactions_json = transactions_to_json(transactions)

    return WEAK_PROMPT_TEMPLATE.format(
        transactions_json=transactions_json
    )


def build_improved_prompt(transactions):
    transactions_json = transactions_to_json(transactions)

    return IMPROVED_PROMPT_TEMPLATE.format(
        transactions_json=transactions_json
    )