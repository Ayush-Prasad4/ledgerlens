from contextlib import contextmanager

from ledgerlens import agent, calculate
from ledgerlens.injection import insert_poison


@contextmanager
def poisoned(case):
    poison, position, path = case["poison"], case["position"], case["path"]
    if path == "lookup":
        target, name = agent, "retrieve"
    elif path == "calc":
        target, name = calculate, "retrieve_for_metrics"
    else:
        raise ValueError(f"unknown path: {path}")
    original = getattr(target, name)
    trace = {"extractor_facts": None, "extractor_error": None, "extractor_chunks": None}

    def wrapper(*args, **kwargs):
        return insert_poison(original(*args, **kwargs), poison, position)

    setattr(target, name, wrapper)

    original_extract = None
    if path == "calc":
        original_extract = calculate.extract_facts

        def extract_wrapper(*args, **kwargs):
            try:
                facts = original_extract(*args, **kwargs)
            except Exception as exc:
                trace["extractor_error"] = f"{type(exc).__name__}: {exc}"
                raise
            trace["extractor_facts"] = [f.get("name") for f in facts if isinstance(f, dict)]
            trace["extractor_chunks"] = {f.get("name"): f.get("chunk_id") for f in facts if isinstance(f, dict)}
            return facts

        calculate.extract_facts = extract_wrapper
    try:
        yield trace
    finally:
        setattr(target, name, original)
        if original_extract is not None:
            calculate.extract_facts = original_extract
