"""Source-document manifest: official links and SHA-256 hashes for every document the figures were read from.

    python scripts/source_documents.py check            # hashes of local copies still in the repository match the manifest
    python scripts/source_documents.py check-remote     # download each official link, compare its hash (needs network)
    python scripts/source_documents.py resolve-ch       # find the document-level Companies House link for each filing,
                                                        # download it and compare with the local copy (needs network)

`check` runs in the tests. The two network commands run in the GitHub workflow "Source documents" and write
data/metadata/source_documents_checked.csv as an artifact; they never delete or commit anything.

verification_status:  verified              official file has the same SHA-256 as the copy used; no copy in the repository
                      candidate_unverified  official link found but not yet compared by hash; copy kept in the
                                            author's private archive, not in the public repository
                      open_data_input       openly licensed file the pipeline reads; kept in the repository
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "metadata" / "source_documents.csv"
CHECKED = ROOT / "data" / "metadata" / "source_documents_checked.csv"
CH = "https://find-and-update.company-information.service.gov.uk"
UA = {"User-Agent": "f1-moneyball research replication (github.com/NahianIbnat-2000/f1-moneyball)"}
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read() -> list[dict]:
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(rows: list[dict], path: Path) -> None:
    cols = list(rows[0].keys())
    for r in rows:
        cols += [k for k in r if k not in cols]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


STATUSES = {"verified", "candidate_unverified", "open_data_input"}


def check() -> int:
    bad = 0
    for r in read():
        p = ROOT / r["path"]
        problem = None
        if r["verification_status"] not in STATUSES:
            problem = f"unknown verification_status {r['verification_status']!r}"
        elif len(r["sha256"]) != 64:
            problem = "no SHA-256 hash"
        elif r["verification_status"] in ("verified", "candidate_unverified") and not r["document_url"].startswith("https://"):
            problem = "no official document link"
        elif r["verification_status"] == "candidate_unverified" and not r["unconfirmed_reason"]:
            problem = "unconfirmed without a recorded reason"
        if problem:
            print(f"INVALID  {r['path']}: {problem}")
            bad += 1
        if r["local_copy"] == "kept":
            if not p.exists():
                print(f"MISSING  {r['path']}")
                bad += 1
            elif sha256(p.read_bytes()) != r["sha256"]:
                print(f"CHANGED  {r['path']}")
                bad += 1
        elif p.exists():
            print(f"PRESENT  {r['path']} is marked {r['local_copy']} but is still in the repository")
            bad += 1
    print("All local copies match the manifest." if not bad else f"{bad} problem(s).")
    return 1 if bad else 0


def check_remote() -> int:
    rows = read()
    for r in rows:
        url = r["document_url"] or ""
        if not url:
            r["remote_check"] = "no document-level link"
            continue
        try:
            h = sha256(fetch(url))
            r["remote_sha256"] = h
            r["remote_check"] = "identical" if h == r["sha256"] else "different bytes"
        except Exception as e:  # noqa: BLE001 - report every failure, never stop
            r["remote_check"] = f"unreachable: {type(e).__name__}"
        time.sleep(1)
    write(rows, CHECKED)
    print_summary(rows)
    return 0


def _made_up_to(text: str) -> str | None:
    m = re.search(r"made up to\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    if not m or m.group(2).lower() not in MONTHS:
        return None
    return f"{m.group(3)}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"


def accounts_links(company: str, max_pages: int = 40) -> dict[str, list[str]]:
    """period end -> document links, read from the public filing-history pages.

    Reads every page until one has no rows: a page without accounts (for example insolvency filings of a dissolved
    company) is not a reason to stop, which is how the first version of this reader missed Caterham's filings.
    """
    out: dict[str, list[str]] = {}
    for page in range(1, max_pages + 1):
        html = fetch(f"{CH}/company/{company}/filing-history?page={page}").decode("utf-8", "replace")
        rows = [r for r in html.split("<tr")[1:] if "filing-history/" in r]
        for row in rows:
            link = re.search(rf'href="(/company/{company}/filing-history/[A-Za-z0-9]+/document\?format=pdf[^"]*)"', row)
            end = _made_up_to(re.sub(r"<[^>]+>", " ", row))
            if link and end:
                out.setdefault(end, []).append(CH + link.group(1).replace("&amp;", "&").replace("&download=0", ""))
        if not rows:
            break
        time.sleep(1)
    return out


def resolve_ch() -> int:
    rows = read()
    cache: dict[str, dict[str, list[str]]] = {}
    for r in rows:
        if r["category"] != "companies_house":
            continue
        try:
            links = cache.setdefault(r["company_number"], accounts_links(r["company_number"]))
        except Exception as e:  # noqa: BLE001
            r["remote_check"] = f"filing history unreachable: {type(e).__name__}"
            continue
        cands = links.get(r["period_end"], [])
        if r["document_url"] and r["document_url"] not in cands:
            cands = [r["document_url"], *cands]          # a link already recorded is checked first
        if not cands:
            r["remote_check"] = "no accounts filing found for this period"
            continue
        r["candidate_links"] = " ".join(cands)
        for url in cands:  # a period can have more than one filing (amended accounts); the hash decides
            try:
                h = sha256(fetch(url))
            except Exception as e:  # noqa: BLE001
                r["remote_check"] = f"document unreachable: {type(e).__name__}"
                continue
            if h == r["sha256"]:
                r["document_url"], r["remote_sha256"], r["remote_check"] = url, h, "identical"
                break
            r["remote_sha256"], r["remote_check"] = h, "different bytes"
            time.sleep(1)
    write(rows, CHECKED)
    print_summary(rows)
    return 0


def print_summary(rows: list[dict]) -> None:
    from collections import Counter
    print(Counter((r["category"], r.get("remote_check", "")) for r in rows))
    print(f"Wrote {CHECKED.relative_to(ROOT)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    sys.exit({"check": check, "check-remote": check_remote, "resolve-ch": resolve_ch}[cmd]())
