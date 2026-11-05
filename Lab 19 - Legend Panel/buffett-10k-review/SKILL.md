---
name: buffett-10k-review
description: Analyze a public company using five years of SEC 10-K facts, deterministic Buffett checks, and a short evidence-bound business memo. Use when asked for a Buffett-style 10-K business review; do not use for valuation or price targets.
---

Use this skill to separate financial computation from investment judgment.

1. Run `scripts/edgar_buffett.py TICKER --output analysis.json`. It downloads only SEC EDGAR company facts using the included identifying User-Agent.
2. Use only the values and XBRL tags printed by the script. Do not estimate a missing fact: preserve `not found` and let dependent checks remain `not known`.
3. Treat these as code-only calculations: revenue, net income, operating cash flow, capital spending, equity, ROE, owner earnings, and the three Buffett checks.
4. Write a short Markdown memo that makes a business-only verdict: **own the business**, **watch it**, or **pass**. Explain the verdict as Buffett-style qualitative judgment, but cite only numbers printed by the script. Do not discuss price, valuation, or forecast returns.
5. Save the memo as `<ticker>_buffett_memo.md` beside `analysis.json`. Before finalizing, use the script's `printed_numbers` field to verify every numeric claim in the memo.

Definitions fixed for this lab:

- Revenue: `RevenueFromContractWithCustomerExcludingAssessedTax`, otherwise `Revenues`.
- Net income: `NetIncomeLoss`.
- Operating cash flow: `NetCashProvidedByUsedInOperatingActivities`.
- Capital spending: `PaymentsToAcquirePropertyPlantAndEquipment`, otherwise `PaymentsToAcquireProductiveAssets`.
- Equity: `StockholdersEquity`.
- ROE: net income / year-end equity. When equity is zero or below, ROE is `not known`.
- Owner earnings: operating cash flow - capital spending.
- Latest 10-K filing wins where a fiscal period appears in multiple filings.
