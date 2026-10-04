import re


class FactError(ValueError):
    pass


def parse_number(raw):
    """'391,035' -> 391035.0 ; '$(1,234)' -> -1234.0"""
    if not isinstance(raw, str):
        raise FactError("number must be a string")
    s = raw.strip().replace("$", "").replace(" ", "")
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1]
    if not re.fullmatch(r"\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?", s):
        raise FactError(f"cannot parse number: {raw!r}")
    value = float(s.replace(",", ""))
    return -value if negative else value


def number_in_text(raw, text):
    """True if raw appears in text as a whole number (not inside a bigger one)."""
    raw = raw.strip()
    if not raw:
        return False
    pattern = r"(?<![\d,.])" + re.escape(raw) + r"(?!\d)(?!,\d)(?!\.\d)"
    for m in re.finditer(pattern, text):
        if "(" in raw:
            return True  # the caller kept the brackets, the match already checked them
        before = text[: m.start()].rstrip(" $")
        after = text[m.end():].lstrip()
        if before.endswith("(") and after.startswith(")"):
            continue  # printed as (123) means negative; a bare 123 would drop the sign
        return True
    return False
