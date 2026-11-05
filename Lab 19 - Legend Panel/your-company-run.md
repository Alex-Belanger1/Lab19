# Your company — NVDA panel run

## Selection

My Project 2 universe includes BIL, IEF, LQD, and VT. I used the global-equity fund, VT. NVIDIA (NVDA) was the largest holding in the current VT holdings data used for this run. NVDA files annual reports with the SEC, so it is eligible for the EDGAR-based panel.

## Panel result

| Investor | Check outcomes | Verdict |
| --- | --- | --- |
| Buffett | pass; not known; not known | not known |
| Cathie Wood | not known; not known | not known |
| Burry | fail; pass | watch |

The missing revenue and capital-spending facts stay visible as `not found` in the fact table and produce `not known` dependent checks. They were not estimated or filled from another source. The three memos are `nvda_buffett_memo.md`, `nvda_cathie_wood_memo.md`, and `nvda_burry_memo.md`; each uses only numbers printed by the panel script.

## Your decision

**Only with a condition:** I would use this panel only to triage Project 2 companies after a human resolves every `not known` result and investigates any failed check; NVDA is not a screen-pass because its record has missing inputs and Burry's cash-conversion check fails.

## Bull case

NVDA passes the Buffett return-on-equity test in every reported year, with ROE ranging from 19.8% to 91.9%. It also passes Burry's latest leverage test: liabilities are 31.5% of equity, well below the screen's maximum.

## Bear case

NVDA fails Burry's cash-conversion check because operating cash flow was $9,108 million versus net income of $9,752 million in the first reported year. The Buffett owner-earnings checks and both Cathie Wood checks are not known because the available EDGAR facts do not provide the needed capital-spending and later-year revenue inputs.
