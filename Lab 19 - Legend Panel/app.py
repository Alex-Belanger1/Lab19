"""Streamlit interface for the Lab 19 three-investor 10-K panel."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
SCRIPT = ROOT / "buffett-10k-review" / "scripts" / "edgar_buffett.py"
INVESTORS = ("Buffett", "Cathie Wood", "Burry")
MEMO_SUFFIXES = {"Buffett": "buffett", "Cathie Wood": "cathie_wood", "Burry": "burry"}


def memo_number_flags(memos: dict[str, str], allowed_values: list[str]) -> dict[str, list[str]]:
    """Return numbers mentioned in each memo that the script did not print."""
    allowed = {value.replace(",", "") for value in allowed_values}
    flags: dict[str, list[str]] = {}
    for investor, memo in memos.items():
        mentioned = re.findall(r"(?<![A-Za-z0-9])\$?([0-9][0-9,]*(?:\.\d+)?)%?(?![-0-9A-Za-z])", memo)
        flags[investor] = sorted({number for number in mentioned if number.replace(",", "") not in allowed})
    return flags


def verdict(results: list[dict]) -> str:
    outcomes = {result["outcome"] for result in results}
    if "fail" in outcomes:
        return "watch"
    if "not known" in outcomes:
        return "not known"
    return "pass"


st.set_page_config(page_title="Three-Investor 10-K Panel", layout="wide")
st.title("Three-Investor 10-K Panel")
st.caption("SEC EDGAR 10-K facts only; educational demonstration, not investment advice.")

ticker = st.text_input("Ticker", "COST").upper().strip()
output_file = ROOT / f"{ticker.lower()}_analysis.json"

if st.button("Download 10-K facts and run panel", type="primary"):
    completed = subprocess.run([sys.executable, str(SCRIPT), ticker, "--output", str(output_file)], capture_output=True, text=True)
    if completed.returncode:
        st.error(completed.stderr or completed.stdout)
    else:
        st.success("SEC EDGAR facts downloaded and all three investors' checks computed.")
        st.code(completed.stdout)

if not output_file.exists():
    st.info("Run the panel above to display the five-year facts, checks, and memos.")
    st.stop()

analysis = json.loads(output_file.read_text(encoding="utf-8"))
rows = analysis["rows"]
frame = pd.DataFrame(rows)
numeric = ["revenue", "net_income", "operating_cash_flow", "capital_spending", "equity", "liabilities", "research_and_development", "roe", "owner_earnings"]
for column in numeric:
    frame[column] = pd.to_numeric(frame[column], errors="coerce")
for column in ["revenue", "net_income", "operating_cash_flow", "capital_spending", "equity", "liabilities", "research_and_development", "owner_earnings"]:
    frame[column] = frame[column] / 1_000_000
frame["roe"] = frame["roe"] * 100

st.subheader(f"{analysis['ticker']} — five fiscal years")
st.line_chart(frame.set_index("fiscal_year_end")[["owner_earnings", "net_income"]], y_label="USD millions")
shown_columns = ["fiscal_year_end"]
for metric in ("revenue", "net_income", "operating_cash_flow", "capital_spending", "equity", "liabilities", "research_and_development"):
    shown_columns.extend([metric, f"{metric}_tag"])
shown_columns.extend(["roe", "owner_earnings"])
st.dataframe(frame[shown_columns], use_container_width=True, hide_index=True)

panel_checks = analysis.get("panel_checks", {"Buffett": analysis["checks"]})
panel_rows = [
    {"Investor": investor, "Check": result["check"], "Outcome": result["outcome"]}
    for investor in INVESTORS
    for result in panel_checks.get(investor, [])
]
st.subheader("Panel checks")
st.dataframe(pd.DataFrame(panel_rows), use_container_width=True, hide_index=True)

verdict_rows = [{"Investor": investor, "Verdict": verdict(panel_checks.get(investor, [{"outcome": "not known"}]))} for investor in INVESTORS]
st.subheader("Verdicts")
st.dataframe(pd.DataFrame(verdict_rows), use_container_width=True, hide_index=True)

memos: dict[str, str] = {}
for investor in INVESTORS:
    memo_path = ROOT / f"{ticker.lower()}_{MEMO_SUFFIXES[investor]}_memo.md"
    memos[investor] = memo_path.read_text(encoding="utf-8") if memo_path.exists() else ""
flags = memo_number_flags(memos, analysis["printed_numbers"])

st.subheader("Investor memos")
columns = st.columns(3)
for column, investor in zip(columns, INVESTORS):
    with column:
        st.markdown(f"### {investor}")
        if memos[investor]:
            st.markdown(memos[investor])
        else:
            st.warning(f"No memo yet. Save it as {ticker.lower()}_{MEMO_SUFFIXES[investor]}_memo.md.")

st.subheader("Unprinted-number flag — all memos")
all_clear = True
for investor in INVESTORS:
    if flags[investor]:
        all_clear = False
        st.error(f"{investor}: numbers not printed by the script — {', '.join(flags[investor])}")
if all_clear:
    st.success("Every number in all three memos was printed by the script.")
