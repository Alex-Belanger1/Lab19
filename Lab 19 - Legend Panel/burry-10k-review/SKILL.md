---
name: burry-10k-review
description: Review five years of 10-K facts through a Michael Burry-style cash-conversion and leverage screen.
---

Use the shared `buffett-10k-review/scripts/edgar_buffett.py` output. It applies the two code-only checks for this lab:

- Operating cash flow was at least net income in every fiscal year.
- Latest liabilities were no more than twice latest equity.

Write `<ticker>_burry_memo.md` using only numbers in `printed_numbers`. Preserve `not known` when an EDGAR fact is unavailable. Use a business-only verdict: **pass**, **watch**, or **not known**; do not discuss valuation, price targets, or forecast returns.
