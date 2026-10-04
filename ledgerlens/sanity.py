import math
import re

from ledgerlens.query_parser import parse_years

_NAME_YEAR_RE = re.compile(r"(?:^|_)(?:fy)?(20\d\d)(?=_|$)")


def _name_year(name):
    years = _NAME_YEAR_RE.findall(name)
    return int(years[-1]) if years else None


def sanity_check(question, calculation):
    """Return (ok, reason) for a finished calculation. No LLM call.

    Checks: every fact name carries a year; the filing the number came from can contain
    that year (a 10-K shows its own year plus up to two earlier ones); every year the
    question asks about is covered by some fact; the result is a finite number.
    It cannot catch a swapped column inside the right filing, the wrong row, or a unit mix-up.
    """
    result = calculation.get("result")
    if not isinstance(result, (int, float)) or not math.isfinite(result):
        return False, "the result is not a finite number"
    covered = set()
    for fact in calculation.get("facts") or []:
        year = _name_year(fact["name"])
        if year is None:
            return False, f"cannot tell which year {fact['name']} is for"
        try:
            filing = int(fact.get("fiscal_year"))
        except (TypeError, ValueError):
            return False, f"unknown filing year for {fact['name']}"
        if not year <= filing <= year + 2:
            return False, f"{fact['name']} is a {year} number but came from the FY{filing} filing"
        covered.add(year)
    missing = sorted(set(parse_years(question)) - covered)
    if missing:
        return False, "no number was used for fiscal " + ", ".join(str(y) for y in missing)
    return True, ""
