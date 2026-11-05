"""Lab 19 V: verify the computed COST panel against the known answer."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).parent
ANALYSIS_PATH = ROOT / "cost_analysis.json"
MEMOS = ("cost_buffett_memo.md", "cost_cathie_wood_memo.md", "cost_burry_memo.md")
EXPECTED = {
    "Buffett": ["pass", "pass", "pass"],
    "Cathie Wood": ["fail", "not known"],
    "Burry": ["pass", "pass"],
}
NUMBER_PATTERN = r"(?<![A-Za-z0-9])[$]?([0-9][0-9,]*(?:\.\d+)?)%?(?![-0-9A-Za-z])"


def main() -> None:
    analysis = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
    assert analysis["ticker"] == "COST", "Run the COST panel before verifying it."

    print("COST panel — known-answer verification")
    for investor, expected in EXPECTED.items():
        actual = [result["outcome"] for result in analysis["panel_checks"][investor]]
        assert actual == expected, f"{investor}: expected {expected}, got {actual}"
        print(f"PASS  {investor}: {', '.join(actual)}")

    metrics = analysis["derived_metrics"]
    assert round(metrics["revenue_growth_annual"] * 100, 1) == 7.5
    assert metrics["rd_to_revenue"] == "not known"
    assert round(metrics["liabilities_to_equity"] * 100, 1) == 148.7
    print("PASS  Revenue growth = 7.5%; R&D/revenue = not known; liabilities/equity = 148.7%")

    allowed = {number.replace(",", "") for number in analysis["printed_numbers"]}
    for filename in MEMOS:
        memo = (ROOT / filename).read_text(encoding="utf-8")
        unprinted = sorted({number for number in re.findall(NUMBER_PATTERN, memo) if number.replace(",", "") not in allowed})
        assert not unprinted, f"{filename}: unprinted numbers {unprinted}"
    print("PASS  All three memos use only script-printed numbers.")
    print("Known answer reproduced.")


if __name__ == "__main__":
    main()
