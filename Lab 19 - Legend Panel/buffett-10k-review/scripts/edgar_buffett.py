"""Compute the Lab 18 Buffett metrics from SEC EDGAR companyfacts data."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENT = "Alex Belanger belangea@purdue.edu"
HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

METRICS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
    "net_income": ["NetIncomeLoss"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capital_spending": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "equity": ["StockholdersEquity"],
    "liabilities": ["Liabilities"],
    "research_and_development": ["ResearchAndDevelopmentExpense"],
}
FLOW_METRICS = {"revenue", "net_income", "operating_cash_flow", "capital_spending", "research_and_development"}
CATHIE_GROWTH_THRESHOLD = 0.15


def get_json(url: str) -> dict:
    request = Request(url, headers=HEADERS)
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"SEC EDGAR request failed: {exc}") from exc


def cik_for_ticker(ticker: str) -> int:
    companies = get_json(TICKERS_URL)
    ticker = ticker.upper()
    for entry in companies.values():
        if entry["ticker"].upper() == ticker:
            return int(entry["cik_str"])
    raise ValueError(f"Ticker not found in SEC ticker map: {ticker}")


def is_one_year_flow(fact: dict) -> bool:
    if not fact.get("start") or not fact.get("end"):
        return False
    days = (datetime.fromisoformat(fact["end"]) - datetime.fromisoformat(fact["start"])).days
    return 320 <= days <= 380


def annual_candidates(units: list[dict], is_flow: bool) -> list[dict]:
    candidates = []
    for fact in units:
        if fact.get("form") != "10-K" or not fact.get("fy") or fact.get("fp") != "FY":
            continue
        if is_flow and not is_one_year_flow(fact):
            continue
        if not is_flow and fact.get("start"):
            continue
        if fact.get("end") and fact.get("val") is not None:
            candidates.append(fact)
    return candidates


def fact_by_fiscal_year(company_facts: dict, metric: str) -> dict[str, dict]:
    us_gaap = company_facts.get("facts", {}).get("us-gaap", {})
    is_flow = metric in FLOW_METRICS
    for tag in METRICS[metric]:
        concept = us_gaap.get(tag)
        if not concept:
            continue
        units = concept.get("units", {}).get("USD", [])
        candidates = annual_candidates(units, is_flow)
        # Latest filing wins for a fiscal period. Keep the period-end label, not calendar year.
        selected: dict[str, dict] = {}
        for item in sorted(candidates, key=lambda x: x.get("filed", ""), reverse=True):
            selected.setdefault(item["end"], {"value": item["val"], "tag": tag, "filed": item.get("filed")})
        if selected:
            return selected
    return {}


def display(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value / 1_000_000:,.0f}"
    return str(value)


def make_rows(company_facts: dict) -> list[dict]:
    values = {metric: fact_by_fiscal_year(company_facts, metric) for metric in METRICS}
    fiscal_ends = sorted({end for metric_values in values.values() for end in metric_values}, reverse=True)[:5]
    rows = []
    for end in sorted(fiscal_ends):
        row = {"fiscal_year_end": end}
        for metric in METRICS:
            item = values[metric].get(end)
            row[metric] = item["value"] if item else "not found"
            row[f"{metric}_tag"] = item["tag"] if item else "not found"
        equity = row["equity"]
        income = row["net_income"]
        ocf = row["operating_cash_flow"]
        capex = row["capital_spending"]
        row["roe"] = income / equity if isinstance(income, (int, float)) and isinstance(equity, (int, float)) and equity > 0 else "not known"
        row["owner_earnings"] = ocf - capex if isinstance(ocf, (int, float)) and isinstance(capex, (int, float)) else "not found"
        rows.append(row)
    return rows


def check_all(rows: list[dict], predicate, field: str, label: str) -> dict:
    values = [row[field] for row in rows]
    if any(not isinstance(value, (int, float)) for value in values):
        outcome = "not known"
    else:
        outcome = "pass" if predicate(values) else "fail"
    return {"check": label, "outcome": outcome}


def check_latest_ratio(rows: list[dict], numerator: str, denominator: str, maximum: float, label: str) -> dict:
    latest = rows[-1]
    top, bottom = latest[numerator], latest[denominator]
    if not isinstance(top, (int, float)) or not isinstance(bottom, (int, float)) or bottom <= 0:
        return {"check": label, "outcome": "not known"}
    return {"check": label, "outcome": "pass" if top / bottom <= maximum else "fail"}


def check_ocf_vs_income(rows: list[dict]) -> dict:
    pairs = [(row["operating_cash_flow"], row["net_income"]) for row in rows]
    if any(not isinstance(ocf, (int, float)) or not isinstance(income, (int, float)) for ocf, income in pairs):
        return {"check": "Operating cash flow at least net income every year", "outcome": "not known"}
    return {"check": "Operating cash flow at least net income every year", "outcome": "pass" if all(ocf >= income for ocf, income in pairs) else "fail"}


def panel_checks(rows: list[dict]) -> dict[str, list[dict]]:
    cathie_revenue = [row["revenue"] for row in rows]
    latest = rows[-1]
    rd, revenue = latest["research_and_development"], latest["revenue"]
    if not isinstance(rd, (int, float)) or not isinstance(revenue, (int, float)) or revenue <= 0:
        rd_check = {"check": "R&D 5% or more of revenue, latest year", "outcome": "not known"}
    else:
        rd_check = {"check": "R&D 5% or more of revenue, latest year", "outcome": "pass" if rd / revenue >= 0.05 else "fail"}
    return {
        "Buffett": [
            check_all(rows, lambda values: all(value >= 0.15 for value in values), "roe", "ROE of 15% or more every year"),
            check_all(rows, lambda values: all(value > 0 for value in values), "owner_earnings", "Owner earnings positive every year"),
            check_all(rows, lambda values: values[-1] > values[0], "owner_earnings", "Owner earnings grew, first year to last"),
        ],
        "Cathie Wood": [
            check_all(rows, lambda values: (values[-1] / values[0]) ** (1 / 4) - 1 >= CATHIE_GROWTH_THRESHOLD, "revenue", "Revenue grew 15% or more a year, first year to last"),
            rd_check,
        ],
        "Burry": [
            check_ocf_vs_income(rows),
            check_latest_ratio(rows, "liabilities", "equity", 2.0, "Liabilities no more than twice equity, latest year"),
        ],
    }


def derived_metrics(rows: list[dict]) -> dict[str, object]:
    first, latest = rows[0], rows[-1]
    revenue_growth = "not known"
    if isinstance(first["revenue"], (int, float)) and isinstance(latest["revenue"], (int, float)) and first["revenue"] > 0:
        revenue_growth = (latest["revenue"] / first["revenue"]) ** (1 / 4) - 1
    rd_to_revenue = "not known"
    if isinstance(latest["research_and_development"], (int, float)) and isinstance(latest["revenue"], (int, float)) and latest["revenue"] > 0:
        rd_to_revenue = latest["research_and_development"] / latest["revenue"]
    liabilities_to_equity = "not known"
    if isinstance(latest["liabilities"], (int, float)) and isinstance(latest["equity"], (int, float)) and latest["equity"] > 0:
        liabilities_to_equity = latest["liabilities"] / latest["equity"]
    return {"revenue_growth_annual": revenue_growth, "rd_to_revenue": rd_to_revenue, "liabilities_to_equity": liabilities_to_equity}


def printed_numbers(rows: list[dict], metrics: dict[str, object]) -> list[str]:
    numbers = {"5", "15"}
    for row in rows:
        for field in ("revenue", "net_income", "operating_cash_flow", "capital_spending", "equity", "liabilities", "research_and_development", "owner_earnings"):
            value = row[field]
            if isinstance(value, (int, float)):
                millions = value / 1_000_000
                numbers.update({f"{millions:,.0f}", f"{millions:.0f}"})
        if isinstance(row["roe"], (int, float)):
            numbers.add(f"{row['roe'] * 100:.1f}")
    for value in metrics.values():
        if isinstance(value, (int, float)):
            numbers.add(f"{value * 100:.1f}")
    return sorted(numbers)


def print_report(ticker: str, company_name: str, rows: list[dict], checks_by_investor: dict[str, list[dict]], metrics: dict[str, object]) -> None:
    print(f"{ticker} — {company_name} | USD millions | SEC EDGAR 10-K facts")
    print("FY end | Revenue [tag] | Net income [tag] | OCF [tag] | Capex [tag] | Equity [tag] | Liabilities [tag] | R&D [tag] | ROE | Owner earnings")
    for row in rows:
        columns = [row["fiscal_year_end"]]
        for metric in ("revenue", "net_income", "operating_cash_flow", "capital_spending", "equity", "liabilities", "research_and_development"):
            columns.append(f"{display(row[metric])} [{row[f'{metric}_tag']}]")
        roe = f"{row['roe'] * 100:.1f}%" if isinstance(row["roe"], (int, float)) else row["roe"]
        columns.extend([roe, display(row["owner_earnings"])])
        print(" | ".join(columns))
    print("\nDerived panel metrics")
    for name, value in metrics.items():
        print(f"- {name}: {value * 100:.1f}%" if isinstance(value, (int, float)) else f"- {name}: {value}")
    for investor, results in checks_by_investor.items():
        print(f"\n{investor} checks")
        for result in results:
            print(f"- {result['check']}: {result['outcome']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", help="NYSE/Nasdaq ticker, e.g. COST")
    parser.add_argument("--output", type=Path, default=Path("analysis.json"), help="JSON output path")
    args = parser.parse_args()
    ticker = args.ticker.upper()
    cik = cik_for_ticker(ticker)
    facts = get_json(FACTS_URL.format(cik=cik))
    rows = make_rows(facts)
    if len(rows) < 5:
        raise RuntimeError(f"Only {len(rows)} annual fiscal years were found for {ticker}; expected five.")
    checks_by_investor = panel_checks(rows)
    metrics = derived_metrics(rows)
    output = {"ticker": ticker, "company_name": facts.get("entityName", ticker), "cik": f"{cik:010d}", "units": "USD millions", "rows": rows, "checks": checks_by_investor["Buffett"], "panel_checks": checks_by_investor, "derived_metrics": metrics, "printed_numbers": printed_numbers(rows, metrics)}
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print_report(ticker, output["company_name"], rows, checks_by_investor, metrics)
    print(f"\nSaved machine-readable results to {args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
