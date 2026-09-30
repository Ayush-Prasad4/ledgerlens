def growth_percent(old, new):
    """Batata hai ki old se new tak kitne percent badha (ya ghata)."""
    if old == 0:
        raise ValueError("old value 0 nahi ho sakti")
    return (new - old) / old * 100
