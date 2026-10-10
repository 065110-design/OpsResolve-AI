# OpsResolve AI — Domain-Expert Multi-Agent Operations Control Tower

**Individual assignment | Tanisha Phogaat | 065110 | Section L | FORE School of Management**

OpsResolve AI is a working educational web app that coordinates six **business-specialist workflow stages** to handle B2B order escalations. It classifies a case, applies transparent SLA/priority policy, identifies an owning department, recommends resolution steps, drafts a customer update, and runs independent safety review. **It never sends an email, processes a refund, or edits an external system.**

## 1. Run the application

Install Python 3.10 or later. Open a terminal in this folder.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Your browser should open the locally served Streamlit app, usually at `http://localhost:8501`.

If the browser does not open, use the Local URL shown in the terminal. Keep the terminal running while demonstrating the project.

### No API key? Use offline demonstration

The default **Offline demonstrator** needs no API key. Its triage, scoring, drafting and QA use deterministic rules and templates rather than a live generative model. The UI labels this mode clearly.

### Enable Gemini specialist reasoning

1. Obtain a Gemini API key from https://aistudio.google.com/apikey.
2. Launch the app, select **Live Gemini specialists** in the sidebar and enter your key into the masked field. The key is not exported.
3. Open **Case Workbench**, select a synthetic case, and choose **Run multi-agent workflow**.
4. Gemini receives the synthetic case description and a policy snapshot, making separate calls for **Triage**, **Resolution/Communication**, and **Independent QA**. Policy scoring and routing always remain deterministic.

**Important:** Live mode requires working internet access, a valid Google API key, quota and access to the configured model (`gemini-2.5-flash`). The model and free-tier availability may change. Any failed live run displays an error; it is never silently passed off as AI output. Do not upload real customer or financial data into this academic prototype.

### Option: Streamlit Community Cloud

Push `app.py`, `agent_engine.py`, `requirements.txt`, `.streamlit/config.toml` to your own GitHub repository; deploy the repository at https://share.streamlit.io/. For live mode, add `GEMINI_API_KEY` as a Streamlit secret rather than committing the actual key. Deployment is not completed by this package. There is no verified public repository URL or live web-app URL yet.

## 2. Suggested 3-minute demonstration

1. **Overview** — point out five fictional cases and priority distribution.
2. **Case Workbench** — select `DEMO-101`, run in offline mode (works immediately).
3. Show the issue category, explain the heuristic 0–100 risk score, identify the department and SLA timing indicator.
4. Show the recommended action plan, editable draft and independent QA warnings.
5. Select **Approve draft for later sending**, click **Record human decision**, and show the local audit log. Stress that no message was sent.
6. Open the **Six-agent reasoning / decision trace** and explain the handoffs.
7. **Batch Analysis** — process or export the demo CSV.
8. Optionally repeat in Gemini mode with a valid API key to show true LLM reasoning.

## 3. Specialist workflow

| Stage | Business expertise | What it produces | AI usage |
|---|---|---|---|
| 1. Intake & Triage | Service triage and taxonomy | Issue category, evidence | Gemini in live / keyword rules offline |
| 2. SLA & Risk | Service operations | P1–P3, illustrative risk score, due times | Policy calculations |
| 3. Ownership & Routing | Process governance | Accountable department | Approved ownership map |
| 4. Resolution Planning | Functional playbooks | Suggested next steps | Gemini in live / rules offline |
| 5. Customer Communications | Customer support | Draft email for review | Gemini in live (shared resolution call) / template offline |
| 6. Safety & QA | Responsible AI and service quality | Checks, warnings, human review state | Gemini review in live + hard rule guardrail |

**The six workflow stages do not imply six separate LLM calls.** There are three specialist model calls in Gemini mode and zero in offline mode. This hybrid design avoids allowing an LLM to invent policies, SLA calculations or accountable owners.

## 4. Illustrative academic policy

- Risk points: impact (5/18/32), case age (0/4/8/12), staleness (0/5/12/18), commercial value (0/4/9/16), critical language (0 or 14). Maximum is 100.
- `P1` for risk ≥ 65; `P2` for 36–64; `P3` for ≤ 35.
- Response target (hours): P1=2, P2=4, P3=8.
- Resolution target = min(category base hours, P1 cap 8h / P2 cap 24h / P3 uncapped).
- Escalation: L2 when illustrative resolution deadline has passed, or P1 response deadline has passed; L1 for remaining escalated/overdue criteria; otherwise owner follow-up.
- The clock is **calendar hours**, not a real organization's business-hour schedule. There is no actual acknowledgment timestamp; "response target elapsed" is **not proof of breach**.
- Risks are deterministic heuristic scores, **not probabilistic forecasts**.

## 5. Files included

- `app.py` — Streamlit front-end and local approval log.
- `agent_engine.py` — orchestrator, domain policy, specialist prompts and analysis engine.
- `tests/test_agents.py` — 16 automated unit/regression tests.
- `data/demo_cases.csv` — five fictional sample cases.
- `data/example_case_output.json` — reproducible offline case trace at a fixed example time.
- The academic PDF report and PPTX presentation are submitted separately; neither is packaged in the application ZIP.

## 6. Verify

```bash
python -m pytest -q
```

Expected for this version: `16 passed`. This tests local logic only; it does **not** validate Gemini API uptime, response quality, legal compliance or effectiveness on real cases.

## 7. Business value, scope and limitations

Potential value includes consistent first-pass classification, clearer ownership, earlier attention to at-risk cases, and faster composition of drafts. Benefits have **not** been measured in a customer deployment. This proof of concept is limited by synthetic cases, illustrative SLAs, heuristics, absence of verified ERP/CRM integration, privacy controls suitable only for a demo, and lack of real human evaluation of generated content. A production version would need role-based access, persistent audit data, approved organizational policies, LLM evaluations, privacy review, and human supervision.

## References

- Google Gen AI Python SDK: https://googleapis.github.io/python-genai/index.html
- Streamlit API: https://docs.streamlit.io/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST Generative AI Profile: https://doi.org/10.6028/NIST.AI.600-1
