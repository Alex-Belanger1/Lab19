# Lab 19 — Floor checkout

| Required evidence | Completed artifact | Result |
| --- | --- | --- |
| COST known answer | `verify_cost_panel.py` | Buffett: 3 pass; Cathie Wood: fail, not known; Burry: 2 pass; memo-number check passes. |
| Your company panel | `nvda_analysis.json` and `your-company-run.md` | NVDA panel run complete; all missing EDGAR facts remain `not found` and dependent checks remain `not known`. |
| Bull and bear | `your-company-run.md` | Two-sentence bull and two-sentence bear cases are tied to the panel facts. |
| Decision | `your-company-run.md` | Conditional triage-only decision; requires human resolution of gaps and investigation of failures. |

Run the two proof commands from this folder:

```powershell
python .\verify_cost_panel.py
python .\buffett-10k-review\scripts\edgar_buffett.py NVDA --output .\nvda_analysis.json
```

Then start the interface with `streamlit run .\app.py`, enter `COST` for the known answer or `NVDA` for the Project 2 company run.
