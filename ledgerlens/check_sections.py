from __future__ import annotations

from ledgerlens.config import RAW_DIR
from ledgerlens.processor import ITEM_ORDER, process_filing


def item_key(title: str) -> str:
    return title.split(".")[0].replace("Item ", "")


def main() -> None:
    for html_path in sorted(RAW_DIR.glob("*/*_10-K.html")):
        ticker = html_path.parent.name
        year = html_path.stem.split("_")[0]
        sections = process_filing(html_path)
        sizes = {item_key(s["title"]): len(s["text"]) for s in sections}
        missing = [key for key in ITEM_ORDER if key not in sizes]

        warnings = []

        if sizes.get("6", 0) > 2000:
            warnings.append("Item 6 bahut bada")

        if sizes.get("7", 10**9) < 8000:
            warnings.append("Item 7 bahut chhota")

        if sizes.get("8", 10**9) < 20000:
            warnings.append("Item 8 bahut chhota")

        print(
            f"{ticker} FY{year}: {len(sections)} sections | "
            f"Item 6: {sizes.get('6', 0):,} | Item 7: {sizes.get('7', 0):,} | "
            f"Item 8: {sizes.get('8', 0):,} | missing: {missing} {warnings}"
        )


if __name__ == "__main__":
    main()
