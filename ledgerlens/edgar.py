import json
import time

import httpx

from ledgerlens.config import RAW_DIR, SEC_USER_AGENT

COMPANIES = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
}

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
DOC_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{doc}"


def find_10k_filings(submissions, cik, limit=3):
    """SEC ke JSON se sirf 10-K filings nikalo (sabse nayi pehle)."""
    recent = submissions["filings"]["recent"]
    found = []
    for i, form in enumerate(recent["form"]):
        if form != "10-K":
            continue
        accession = recent["accessionNumber"][i]
        doc = recent["primaryDocument"][i]
        report_date = recent["reportDate"][i]
        found.append(
            {
                "form": form,
                "accession": accession,
                "report_date": report_date,
                "fiscal_year": int(report_date[:4]),
                "url": DOC_URL.format(
                    cik_int=int(cik),
                    acc_nodash=accession.replace("-", ""),
                    doc=doc,
                ),
            }
        )
        if len(found) == limit:
            break
    return found


def download_all(limit=3):
    if not SEC_USER_AGENT:
        raise SystemExit("Pehle .env file mein SEC_USER_AGENT daalo (naam + email).")

    headers = {"User-Agent": SEC_USER_AGENT}
    with httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client:
        for ticker, cik in COMPANIES.items():
            resp = client.get(SUBMISSIONS_URL.format(cik=cik))
            resp.raise_for_status()
            filings = find_10k_filings(resp.json(), cik, limit)
            time.sleep(0.2)

            folder = RAW_DIR / ticker
            folder.mkdir(parents=True, exist_ok=True)
            for f in filings:
                html_path = folder / f"{f['fiscal_year']}_10-K.html"
                if html_path.exists():
                    print("skip (pehle se hai):", html_path.name)
                    continue
                r = client.get(f["url"])
                r.raise_for_status()
                html_path.write_text(r.text, encoding="utf-8")
                info = {**f, "ticker": ticker, "cik": cik}
                info_path = folder / f"{f['fiscal_year']}_10-K.json"
                info_path.write_text(json.dumps(info, indent=2))
                print("saved:", ticker, html_path.name)
                time.sleep(0.2)


if __name__ == "__main__":
    download_all()
