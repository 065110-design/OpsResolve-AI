from datetime import datetime, timedelta, timezone
import pytest
from agent_engine import (Ticket, CATEGORIES, classify_offline, policy_agent, offline_qa,
                          demo_tickets, batch_offline, run_workflow, as_markdown)

NOW = datetime(2026, 10, 10, 11, 0, tzinfo=timezone.utc)


def make_ticket(description="Shipment delayed; carrier ETA still pending.", stage="Shipping", impact="Medium",
                hours_open=10, hours_stale=3, value=5000, category="Auto-detect"):
    return Ticket("TEST-001", "Fictional Client", stage, description, impact, value,
                  NOW - timedelta(hours=hours_open), NOW - timedelta(hours=hours_stale), category)


def test_demo_has_synthetic_cases():
    assert len(demo_tickets(NOW)) == 5


def test_keyword_classification_shipping():
    assert classify_offline(make_ticket())["category"] == "Delivery Delay"


def test_keyword_classification_credit():
    assert classify_offline(make_ticket("Invoice payment and remittance outstanding", "Payment"))["category"] == "Payment / Credit"


def test_manual_category_override():
    assert classify_offline(make_ticket(category="Product Quality"))["category"] == "Product Quality"


def test_stage_based_fallback():
    assert classify_offline(make_ticket("Need update.", "Quotation"))["category"] == "Quotation Delay"


def test_risk_is_bounded():
    case = make_ticket("Critical urgent cancellation; shipment stuck", "Shipping", "High", 200, 40, 100000)
    policy = policy_agent(case, "Delivery Delay", NOW)
    assert 0 <= policy["risk_score"] <= 100 and policy["priority"] == "P1"


def test_priority_escalation_boundary():
    case = make_ticket("Shipment urgent", "Shipping", "High", 60, 26, 62000)
    p = policy_agent(case, "Delivery Delay", NOW)
    assert p["resolution_target_elapsed"] is True
    assert p["escalation"].startswith("L2")


def test_owner_from_approved_policy():
    p = policy_agent(make_ticket(), "Payment / Credit", NOW)
    assert p["owner"] == "Finance / Credit Control"


def test_clock_time_target():
    case = make_ticket(hours_open=2, hours_stale=1, impact="Low", value=0)
    p = policy_agent(case, "Delivery Delay", NOW)
    assert p["resolution_target_hours"] == 48
    assert p["resolution_target_elapsed"] is False


def test_qa_flags_unapproved_refund():
    draft = {"customer_draft":"Your refund approved and guaranteed delivery is confirmed."}
    p = policy_agent(make_ticket(), "Product Quality", NOW)
    qa=offline_qa(draft,p)
    assert qa["approved_for_human_review"] is False and len(qa["flags"]) >= 2


def test_validation_invalid_clock():
    with pytest.raises(ValueError):
        make_ticket(hours_open=2,hours_stale=4).validate(NOW)


def test_validation_missing_description():
    with pytest.raises(ValueError):
        make_ticket(description="").validate(NOW)


def test_six_stage_trace():
    result=run_workflow(make_ticket(),mode="offline",now=NOW)
    assert len(result["trace"]) == 6
    assert "Offline" in result["mode"]
    assert "No external action" in result["safety"]


def test_batch_matches_number_of_inputs():
    result=batch_offline(demo_tickets(NOW),now=NOW)
    assert len(result)==5 and all(row["Priority"] in {"P1","P2","P3"} for row in result)


def test_brief_contains_human_control():
    brief=as_markdown(run_workflow(make_ticket(),mode="offline",now=NOW))
    assert "approval required" in brief.lower()


def test_live_without_key_rejected():
    with pytest.raises(ValueError):
        run_workflow(make_ticket(),mode="live",api_key="",now=NOW)
