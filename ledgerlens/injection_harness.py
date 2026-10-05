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

    def wrapper(*args, **kwargs):
        return insert_poison(original(*args, **kwargs), poison, position)

    setattr(target, name, wrapper)
    try:
        yield
    finally:
        setattr(target, name, original)
