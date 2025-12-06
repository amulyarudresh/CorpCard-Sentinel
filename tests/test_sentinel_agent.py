import pytest
from unittest.mock import MagicMock
from corpcard_sentinel.sentinel_agent import monitor, evaluate, investigate, enforce, AgentState, decide_next_step
from corpcard_sentinel.models import CardStatus, User, Transaction

def test_monitor():
    state = AgentState(
        transaction={"id": 1, "amount": 100},
        policies=[],
        violation_reason=None,
        is_violation=False,
        investigation_count=0,
        spending_history=None,
        decision=None
    )
    new_state = monitor(state)
    assert new_state == state

def test_evaluate_safe(mocker):
    mock_llm = mocker.patch("corpcard_sentinel.sentinel_agent.llm")
    mock_llm.invoke.return_value.content = '{"decision": "SAFE", "reason": "All good"}'
    
    state = AgentState(
        transaction={"id": 1, "amount": 100},
        policies=["Rule 1"],
        violation_reason=None,
        is_violation=False,
        investigation_count=0,
        spending_history=None,
        decision=None
    )
    
    new_state = evaluate(state)
    assert new_state["decision"] == "SAFE"
    assert new_state["is_violation"] is False

def test_evaluate_violation(mocker):
    mock_llm = mocker.patch("corpcard_sentinel.sentinel_agent.llm")
    mock_llm.invoke.return_value.content = '{"decision": "VIOLATION", "reason": "Bad stuff"}'
    
    state = AgentState(
        transaction={"id": 1, "amount": 100},
        policies=["Rule 1"],
        violation_reason=None,
        is_violation=False,
        investigation_count=0,
        spending_history=None,
        decision=None
    )
    
    new_state = evaluate(state)
    assert new_state["decision"] == "VIOLATION"
    assert new_state["is_violation"] is True
    assert new_state["violation_reason"] == "Bad stuff"

def test_evaluate_suspicious_initial(mocker):
    mock_llm = mocker.patch("corpcard_sentinel.sentinel_agent.llm")
    mock_llm.invoke.return_value.content = '{"decision": "SUSPICIOUS", "reason": "Weird"}'
    
    state = AgentState(
        transaction={"id": 1, "amount": 100},
        policies=["Rule 1"],
        violation_reason=None,
        is_violation=False,
        investigation_count=0,
        spending_history=None,
        decision=None
    )
    
    new_state = evaluate(state)
    assert new_state["decision"] == "SUSPICIOUS"
    assert new_state["is_violation"] is False

def test_evaluate_suspicious_limit_reached(mocker):
    mock_llm = mocker.patch("corpcard_sentinel.sentinel_agent.llm")
    mock_llm.invoke.return_value.content = '{"decision": "SUSPICIOUS", "reason": "Still weird"}'
    
    state = AgentState(
        transaction={"id": 1, "amount": 100},
        policies=["Rule 1"],
        violation_reason=None,
        is_violation=False,
        investigation_count=1, # Limit reached
        spending_history=None,
        decision=None
    )
    
    new_state = evaluate(state)
    assert new_state["decision"] == "VIOLATION" # Fails closed
    assert new_state["is_violation"] is True

def test_investigate(mocker):
    mock_get_history = mocker.patch("corpcard_sentinel.sentinel_agent.get_user_spending_history")
    mock_get_history.return_value = "History data"
    mocker.patch("corpcard_sentinel.sentinel_agent.database.SessionLocal")
    
    state = AgentState(
        transaction={"user_id": 123},
        policies=[],
        violation_reason=None,
        is_violation=False,
        investigation_count=0,
        spending_history=None,
        decision=None
    )
    
    new_state = investigate(state)
    assert new_state["spending_history"] == "History data"
    assert new_state["investigation_count"] == 1

def test_enforce_violation(mocker):
    mock_db = MagicMock()
    mocker.patch("corpcard_sentinel.sentinel_agent.database.SessionLocal", return_value=mock_db)
    
    mock_user = User(id=1, card_status=CardStatus.ACTIVE)
    mock_trans = Transaction(id=10, is_violation=False)
    
    # Mock query results
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_trans]
    
    state = AgentState(
        transaction={"user_id": 1, "id": 10},
        policies=[],
        violation_reason="Gambling",
        is_violation=True,
        investigation_count=0,
        spending_history=None,
        decision="VIOLATION"
    )
    
    enforce(state)
    
    assert mock_user.card_status == CardStatus.FROZEN
    assert mock_trans.is_violation is True
    assert mock_trans.violation_reason == "Gambling"
    mock_db.commit.assert_called_once()

def test_decide_next_step():
    assert decide_next_step({"decision": "VIOLATION"}) == "enforce"
    assert decide_next_step({"decision": "SUSPICIOUS"}) == "investigate"
    assert decide_next_step({"decision": "SAFE"}) == "__end__"
    assert decide_next_step({"decision": "MANUAL_REVIEW"}) == "enforce"

def test_evaluate_exception_fail_open(mocker):
    # Mock LLM to raise an exception
    mock_llm = mocker.patch("corpcard_sentinel.sentinel_agent.llm")
    mock_llm.invoke.side_effect = Exception("API Down")
    
    state = AgentState(
        transaction={"id": 1, "amount": 100},
        policies=["Rule 1"],
        violation_reason=None,
        is_violation=False,
        investigation_count=0,
        spending_history=None,
        decision=None
    )
    
    new_state = evaluate(state)
    
    # Assert Fail-Open behavior
    assert new_state["decision"] == "MANUAL_REVIEW"
    assert new_state["is_violation"] is False
    assert "MANUAL REVIEW REQUIRED" in new_state["violation_reason"]

def test_enforce_manual_review(mocker):
    mock_db = MagicMock()
    mocker.patch("corpcard_sentinel.sentinel_agent.database.SessionLocal", return_value=mock_db)
    
    mock_user = User(id=1, card_status=CardStatus.ACTIVE)
    mock_trans = Transaction(id=10, is_violation=False)
    
    # Mock query results based on call order
    # enforce calls queries somewhat independently for user and transaction
    
    # We need to ensure the mocks return what we expect when called.
    # The logic queries User then Transaction.
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_trans] 
    # NOTE: In MANUAL_REVIEW branch, it DOES NOT query/freeze User, only updates Transaction.
    # So we only provide one side effect result for the transaction query.
    
    state = AgentState(
        transaction={"user_id": 1, "id": 10},
        policies=[],
        violation_reason="MANUAL REVIEW REQUIRED: API Down",
        is_violation=False,
        investigation_count=0,
        spending_history=None,
        decision="MANUAL_REVIEW"
    )
    
    enforce(state)
    
    # User should NOT be frozen
    assert mock_user.card_status == CardStatus.ACTIVE 
    
    # Transaction should be updated but NOT as violation
    assert mock_trans.is_violation is False
    assert mock_trans.violation_reason == "MANUAL REVIEW REQUIRED: API Down"
    mock_db.commit.assert_called_once()
