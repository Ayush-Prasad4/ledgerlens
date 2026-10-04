import re

COMPANIES = {
    "AAPL": ["aapl", "apple"],
    "GOOGL": ["googl", "goog", "alphabet", "google"],
    "AMZN": ["amzn", "amazon"],
    "META": ["meta", "facebook"],
    "MSFT": ["msft", "microsoft"],
}
# month in which each company's fiscal year ends
FYE_MONTH = {"AAPL": 9, "GOOGL": 12, "AMZN": 12, "META": 12, "MSFT": 6}
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}

YEAR_RE = re.compile(r"(?:fiscal(?:\s+year)?|fy)\s*'?(20\d\d)", re.IGNORECASE)
DATE_RE = re.compile(r"\b(" + "|".join(MONTHS) + r")\s+(?:\d{1,2},?\s+)?(20\d\d)\b", re.IGNORECASE)


def _find_ticker(question):
    """Return the one company named in the question, or None if missing or ambiguous."""
    q = question.lower()
    found = {
        t for t, names in COMPANIES.items()
        if any(re.search(rf"\b{re.escape(n)}\b", q) for n in names)
    }
    return next(iter(found)) if len(found) == 1 else None


def parse_query(question):
    """Return (ticker, fiscal_year); each is None when missing or ambiguous."""
    ticker = _find_ticker(question)

    year = None
    m = YEAR_RE.search(question)
    if m:
        year = int(m.group(1))
    elif ticker:
        # fallback: a date in the company's fiscal-year-end month gives the fiscal year
        for d in DATE_RE.finditer(question):
            if MONTHS[d.group(1).lower()] == FYE_MONTH[ticker]:
                year = int(d.group(2))
                break
    if year is None:
        # last resort: exactly one year anywhere in the question (e.g. "in 2024")
        years = parse_years(question)
        if len(years) == 1:
            year = years[0]
    return ticker, year


RANGE_RE = re.compile(
    r"(?:fiscal(?:\s+year)?|fy)\s*'?(20\d\d)\s*"
    r"(?:to|and|through|vs\.?|versus|-|–)\s*"
    r"(?:(?:fiscal(?:\s+year)?|fy)\s*)?'?(20\d\d)",
    re.IGNORECASE,
)


BARE_YEAR_RE = re.compile(r"\b(20\d\d)\b")


def parse_years(question):
    """Return every fiscal year mentioned in the question, sorted (may be empty).

    Counts: "fiscal 2024"/"FY2024", ranges like "fiscal 2023 to 2024", dates in the
    company's fiscal-year-end month, and bare years that are not part of a date.
    """
    years = {int(m.group(1)) for m in YEAR_RE.finditer(question)}
    years |= {int(m.group(2)) for m in RANGE_RE.finditer(question)}
    ticker = _find_ticker(question)
    if ticker:
        for d in DATE_RE.finditer(question):
            if MONTHS[d.group(1).lower()] == FYE_MONTH[ticker]:
                years.add(int(d.group(2)))
    without_dates = DATE_RE.sub(" ", question)
    years |= {int(m.group(1)) for m in BARE_YEAR_RE.finditer(without_dates)}
    return sorted(years)
