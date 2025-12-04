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
