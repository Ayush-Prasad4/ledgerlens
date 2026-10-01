from __future__ import annotations

from ledgerlens.config import RAW_DIR
from ledgerlens.processor import ITEM_ORDER, process_filing


def main() -> None:
    for html_path in sorted(RAW_DIR.glob("*/*_10-K.html")):
        ticker = html_path.parent.name
        year = html_path.stem.split("_")[0]
        sections = process_filing(html_path)
        found = {s["title"].split(".")[0].replace("Item ", "") for s in sections}
        missing = [key for key in ITEM_ORDER if key not in found]
        print(f"{ticker} FY{year}: {len(sections)} sections, missing: {missing}")


if __name__ == "__main__":
    main()
