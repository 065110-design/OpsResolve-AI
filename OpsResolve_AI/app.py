"""OpsResolve AI | Streamlit decision-support demonstrator.
Launch with: streamlit run app.py
No outbound messages, tickets, or other business records are updated.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import pandas as pd
import streamlit as st

from agent_engine import (Ticket, STAGES, IMPACTS, CATEGORIES, run_workflow,
                          demo_tickets, batch_offline, as_markdown, ticket_as_dict)

st.set_page_config(page_title="OpsResolve AI | Multi-Agent Operations", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] {font-family:'DM Sans',sans-serif;}
[data-testid="stAppViewContainer"] {background:#f5f7fb;}
[data-testid="stSidebar"] {background:#11213d;}
[data-testid="stSidebar"] * {color:#eaf1ff !important;}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif;color:#14233e;letter-spacing:-.025em;}
.block-container {padding-top:1.35rem;padding-bottom:2rem;max-width:1350px;}
.hero {border-radius:22px;background:linear-gradient(115deg,#172e56 10%,#254987 70%,#2562a8 100%);color:white;padding:28px 34px;margin-bottom:20px;box-shadow:0 13px 32px #193d7226;}
.hero h1{color:white;font-size:2.08rem;margin:0 0 8px 0;}.hero p{opacity:.89;margin:0;font-size:1.01rem;}
.subtag {font-weight:700;text-transform:uppercase;letter-spacing:.18em;color:#a5f3e0;font-size:.75rem;margin-bottom:8px;}
div[data-testid="stMetric"] {background:white;border:1px solid #e4eaf3;border-radius:16px;padding:16px 20px;box-shadow:0 2px 10px #172f4d0a;}
div[data-testid="stMetricLabel"] {font-weight:600;color:#62728e;}
div[data-testid="stMetricValue"] {font-family:'Space Grotesk',sans-serif;color:#142b4f;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:#e5eaf3 !important;border-radius:16px;}
.stButton>button[kind="primary"]{background:#1e5aa7;border-radius:10px;border:0;font-weight:700;}
.stButton>button{border-radius:10px;font-weight:600;}
.agent-label {font-weight:700;color:#22487c;letter-spacing:.02em;}
.helper {font-size:.88rem;color:#61748c;}
</style>
""", unsafe_allow_html=True)

now = datetime.now(timezone.utc)
if "approval_log" not in st.session_state:
    st.session_state.approval_log = []

with st.sidebar:
    st.markdown("## 🧭 OpsResolve AI")
    st.caption("Domain-expert multi-agent control tower")
    st.markdown("---")
    page = st.radio("Workspace", ["Overview", "Case Workbench", "Batch Analysis", "Methodology & Safety"], index=0)
    st.markdown("---")
    st.markdown("#### Inference mode")
    mode_label = st.radio("Select engine", ["Offline demonstrator", "Live Gemini specialists"], help="Offline uses transparent rules and templates, not LLM inference. Live invokes three distinct Gemini specialist calls.")
    live = mode_label.startswith("Live")
    default_key = os.environ.get("GEMINI_API_KEY", "")
    try:
        if not default_key: default_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception: pass
    api_key = st.text_input("Gemini API key", value=default_key, type="password", disabled=not live, help="Get a key from Google AI Studio. Do not use real customer data in this demo.")
    if live and not api_key:
        st.warning("Enter an API key to run live specialists.")
    st.caption("No email is sent; all messages remain drafts.")
    st.markdown("---")
    st.caption("Educational prototype | Synthetic cases only")

st.markdown("""<div class="hero"><div class="subtag">BUSINESS INTELLIGENCE · MULTI-AGENT WORKFLOW</div>
<h1>OpsResolve AI</h1><p>From unresolved B2B order cases to accountable action plans — with SLA control, expert agents, and a human approval gate.</p></div>""", unsafe_allow_html=True)

samples = demo_tickets(now)
if page == "Overview":
    rows = batch_offline(samples, now)
    df = pd.DataFrame(rows)
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Synthetic cases",len(df))
    m2.metric("P1 / critical",int((df['Priority']=='P1').sum()))
    m3.metric("Target time elapsed",int(df['Resolution target elapsed'].sum()))
    m4.metric("Specialist agents",6)
    st.subheader("Operational cockpit")
    left,right=st.columns([1.65,1],gap="large")
    with left:
        st.dataframe(df,hide_index=True,use_container_width=True,height=300)
        st.caption("Illustrative data and SLA policy; not connected to a real company or order database.")
    with right:
        st.markdown("#### Case distribution")
        st.bar_chart(df['Category'].value_counts(),horizontal=True,color='#3c81b8')
        st.markdown("**What makes this agentic?**")
        st.markdown("Independent specialist stages hand off structured findings to an orchestrator. Risk and ownership remain policy-controlled; generation is optional and reviewed.")
    st.info("**To demonstrate:** open **Case Workbench**, choose DEMO-101, run the six-stage workflow and show the resulting plan, customer draft, quality review and decision trace.")

elif page == "Case Workbench":
    st.subheader("Case workbench")
    first, second = st.columns([1.22,1], gap="large")
    with first:
        st.markdown("#### Case input")
        case = st.selectbox("Load synthetic case", ["DEMO-101", "DEMO-102", "DEMO-103", "DEMO-104", "DEMO-105", "Custom case"])
        selected = next((t for t in samples if t.ticket_id==case),None)
        ticket_id = st.text_input("Ticket reference",value=selected.ticket_id if selected else "CUSTOM-001")
        customer=st.text_input("Customer (fictional)",value=selected.customer if selected else "Example Manufacturing Co.")
        stage=st.selectbox("Current order stage",STAGES,index=STAGES.index(selected.stage) if selected else 3)
        category=st.selectbox("Issue category",["Auto-detect"]+CATEGORIES)
        desc=st.text_area("Issue description",value=selected.description if selected else "Shipment is delayed; need verified warehouse dispatch and revised ETA.",height=124)
        c1,c2=st.columns(2)
        with c1:
            impact=st.selectbox("Business impact",IMPACTS,index=IMPACTS.index(selected.impact) if selected else 1)
            order_value=st.number_input("Order value (USD)",min_value=0.0,max_value=1e9,value=float(selected.order_value_usd) if selected else 5000.0,step=100.0)
        with c2:
            age=st.number_input("Hours since opened",min_value=0,max_value=20000,value=int((now-selected.opened_at).total_seconds()/3600) if selected else 12)
            stale=st.number_input("Hours since last update",min_value=0,max_value=20000,value=int((now-selected.last_updated_at).total_seconds()/3600) if selected else 5)
        go=st.button("▶ Run multi-agent workflow",type="primary",use_container_width=True)
    with second:
        st.markdown("#### Specialist orchestration")
        stages=[("01","Intake & Triage","Determine issue taxonomy and urgency signals"),
                ("02","SLA & Risk","Apply auditable policy and deadline tests"),
                ("03","Ownership & Routing","Assign accountable specialist team"),
                ("04","Resolution Planning","Recommend evidence-based next steps"),
                ("05","Customer Communication","Draft a cautious, clear update"),
                ("06","Safety & QA","Review unsupported claims and hold for approval")]
        for number,name,detail in stages:
            st.markdown(f"**{number} · {name}**  ")
            st.caption(detail)
        st.markdown("---")
        st.info("**Live mode:** the triage, resolution and independent QA specialist agents use separate Gemini requests. SLA and routing are enforced by deterministic policy; communications are generated within the resolution step and separately reviewed.")
        st.caption("Synthetic-only demonstration. Do not submit confidential commercial or personally identifying information to external APIs.")

    if go:
        if stale>age:
            st.error("Hours since last update cannot exceed hours since opening.")
        elif live and not api_key:
            st.error("Live mode requires a valid Gemini API key. Switch to offline mode for immediate demonstration.")
        else:
            ticket=Ticket(ticket_id,customer,stage,desc,impact,order_value,
                        now-timedelta(hours=int(age)),now-timedelta(hours=int(stale)),category)
            try:
                with st.spinner("Coordinating six specialist steps..."):
                    result=run_workflow(ticket,mode="live" if live else "offline",api_key=api_key,model="gemini-2.5-flash",now=now)
                st.session_state.case_result=result
                st.session_state.case_key=ticket_id
            except Exception as exc:
                st.error(f"Could not process this case: {type(exc).__name__}: {str(exc)[:240]}")
                st.caption("No automatic fallback to offline occurs in live mode, so results are never represented as Gemini-generated when no model call succeeded.")

    result=st.session_state.get("case_result")
    if result:
        p=result['policy'];r=result['resolution'];q=result['qa']
        st.markdown("---")
        st.subheader(f"Decision brief · {result['ticket']['ticket_id']}")
        k1,k2,k3,k4=st.columns(4)
        k1.metric("Priority",p['priority']);k2.metric("Risk score",f"{p['risk_score']}/100")
        k3.metric("Resolution target",f"{p['resolution_target_hours']} h")
        k4.metric("Review gate","Flagged" if q['flags'] else "Ready")
        st.warning("**Target elapsed** is a policy timing indicator, not proof of a breached response promise. Actual acknowledgement timestamps are unavailable in this educational dataset.") if p['resolution_target_elapsed'] else None
        a,b=st.columns([1.15,1],gap="large")
        with a:
            st.markdown("#### Assignment and next-best action")
            st.markdown(f"**Issue:** {p['category']}  \n**Owner team:** {p['owner']}  \n**Escalation:** {p['escalation']}")
            st.markdown("**Recommended actions**")
            for i,step in enumerate(r['next_steps'],1): st.markdown(f"{i}. {step}")
            with st.expander("Transparent risk factors & SLA computation"):
                st.json({'components':p['risk_components'],'response_target_hours':p['response_target_hours'],
                         'resolution_due_utc':p['resolution_due_utc'],'response_target_elapsed':p['response_target_elapsed'],
                         'policy_note':p['policy_note']})
        with b:
            st.markdown("#### Customer update — draft only")
            draft=st.text_area("Edit before approving",value=r['customer_draft'],height=230,key=f"draft_{result['ticket']['ticket_id']}_{result['processed_at_utc']}")
            if q['flags']:
                st.error("QA warnings: "+" | ".join(q['flags']))
            else: st.success("Quality checks completed. Final human verification still required.")
            decision=st.radio("Human disposition",["Pending review", "Approve draft for later sending", "Reject / request revision"],horizontal=False,key=f"decision_{result['ticket']['ticket_id']}")
            notes=st.text_input("Reviewer / revision notes (optional)",key=f"notes_{result['ticket']['ticket_id']}")
            if st.button("Record human decision",disabled=decision=="Pending review"):
                st.session_state.approval_log.append({'ticket':result['ticket']['ticket_id'],'decision':decision,
                    'notes':notes,'timestamp_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    'draft':draft})
                st.success("Decision saved to this session's local audit log. No email was sent.")
            st.download_button("Download case brief (.md)",as_markdown(result),file_name=f"{result['ticket']['ticket_id']}_decision_brief.md",mime="text/markdown")
        with st.expander("Six-agent reasoning / decision trace",expanded=False):
            for event in result['trace']:
                st.markdown(f"**{event['agent']}**");st.json(event['result'])
        if st.session_state.approval_log:
            with st.expander("Human decision audit log"):
                st.dataframe(pd.DataFrame(st.session_state.approval_log).drop(columns=['draft']),hide_index=True,use_container_width=True)

elif page == "Batch Analysis":
    st.subheader("Batch case triage")
    st.write("Analyze a small CSV batch with the **offline policy engine**. Uploaded files are processed in-session; nothing is transmitted to a third-party model.")
    sample_records=[]
    for t in samples:
        sample_records.append({'ticket_id':t.ticket_id,'customer':t.customer,'stage':t.stage,
          'description':t.description,'impact':t.impact,'order_value_usd':t.order_value_usd,
          'hours_open':int((now-t.opened_at).total_seconds()/3600),
          'hours_since_update':int((now-t.last_updated_at).total_seconds()/3600)})
    template_df=pd.DataFrame(sample_records)
    st.download_button("Download sample CSV template",template_df.to_csv(index=False),"opsresolve_demo_tickets.csv","text/csv")
    upload=st.file_uploader("Upload cases (.csv; up to 100 rows)",type=['csv'])
    try:
        inp=pd.read_csv(upload) if upload is not None else template_df
        required=list(template_df.columns)
        missing=[key for key in required if key not in inp.columns]
        if missing: st.error("Missing fields: "+", ".join(missing))
        elif len(inp)>100: st.error("A maximum of 100 cases is supported in this demonstrator.")
        else:
            st.dataframe(inp.head(10),hide_index=True,use_container_width=True)
            if st.button("Analyze batch",type="primary"):
                tk=[];errors=[]
                for index,row in inp.iterrows():
                    try:
                        t=Ticket(str(row['ticket_id']),str(row['customer']),str(row['stage']),str(row['description']),str(row['impact']),
                           float(row['order_value_usd']),now-timedelta(hours=float(row['hours_open'])),
                           now-timedelta(hours=float(row['hours_since_update'])))
                        t.validate(now);tk.append(t)
                    except Exception as exc: errors.append(f"Row {index+2}: {str(exc)[:110]}")
                output=pd.DataFrame(batch_offline(tk,now)) if tk else pd.DataFrame()
                if errors: st.warning("Rejected rows: "+"; ".join(errors[:8]))
                st.session_state.batch_results=output
            if 'batch_results' in st.session_state and not st.session_state.batch_results.empty:
                out=st.session_state.batch_results
                st.subheader("Results")
                st.dataframe(out,hide_index=True,use_container_width=True)
                st.download_button("Download triage results (.csv)",out.to_csv(index=False),"opsresolve_batch_output.csv","text/csv")
    except Exception as exc:
        st.error(f"Unable to read CSV: {type(exc).__name__}: {str(exc)[:200]}")

else:
    st.subheader("Methodology, architecture & academic limitations")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("#### Design pattern")
        st.markdown("**Coordinator → specialist handoffs → deterministic policy → independent QA → human decision.**")
        st.markdown("In live mode, specialist prompts are invoked separately; the triage model selects among a constrained taxonomy while the policy layer owns all SLA calculations and assignments.")
        st.markdown("#### Business process")
        st.markdown("B2B RFQ/order → issue logged → case classified → risk and SLA assessed → accountable team assigned → resolution planned → customer draft proposed → QA → agent review.")
    with c2:
        st.markdown("#### Safeguards")
        st.markdown("- Synthetic data used for all included cases.\n- No automatic customer messaging, refunds or order updates.\n- No assumed live ERP/CRM integration.\n- Live Gemini requires an API key and network access.\n- Deterministic outputs remain distinguishable from LLM outputs.\n- Risk score is a heuristic, **not a predicted likelihood**.")
        st.markdown("#### Evaluation")
        st.markdown("Run `pytest -q` to execute boundary and regression tests. The detailed report explains the test design, case walkthrough and deployment limitations.")
    st.markdown("---")
    st.caption("Project author: Tanisha Phogaat | Roll 065110 | Section L | FORE School of Management | October 2026")
