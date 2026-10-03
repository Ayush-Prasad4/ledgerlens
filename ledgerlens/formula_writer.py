import json
import re

from ledgerlens.ask import LLM_MODEL, get_llm

MAX_LEN = 200
ALLOWED_CONSTANTS = {1.0, 2.0, 100.0, 1000.0}
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NUM = re.compile(r"\d+(?:\.\d+)?")

FORMULA_SYSTEM = (
    "You write one arithmetic formula that answers a question using verified numbers. "
    'Reply with ONLY a JSON object: {"expression": "..."}. '
    "Use only the fact names given, the operators + - * / and parentheses. "
    "The only plain numbers you may use are 1, 2, 100 and 1000 "
    "(for example * 100 turns a ratio into a percent). "
    "Growth or percent change = (new - old) / old * 100. "
    "Never write the result itself."
)


class FormulaError(ValueError):
    pass


def parse_expression(text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        raise FormulaError("formula writer did not return JSON") from None
    expression = data.get("expression") if isinstance(data, dict) else None
    if not isinstance(expression, str) or not expression.strip():
        raise FormulaError("formula writer returned no expression")
    expression = expression.strip()
    if len(expression) > MAX_LEN:
        raise FormulaError("expression too long")
    for number in _NUM.findall(_IDENT.sub(" ", expression)):
        if float(number) not in ALLOWED_CONSTANTS:
            raise FormulaError(f"number not allowed in formula: {number}")
    return expression


def build_facts_text(facts):
    return "\n".join(
        f"- {f['name']} = {f['value']:.10g} ({f.get('ticker')} FY{f.get('fiscal_year')})"
        for f in facts
    )


def write_formula(question, facts):
    user = f"Question: {question}\n\nVerified facts:\n{build_facts_text(facts)}"
    try:
        response = get_llm().chat.completions.create(
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": FORMULA_SYSTEM},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content
    except Exception as exc:
        raise FormulaError(f"LLM call failed: {exc}") from exc
    return parse_expression(content)
