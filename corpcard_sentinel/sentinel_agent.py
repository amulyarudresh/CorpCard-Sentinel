import os
import json
from typing import TypedDict, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

from . import models, database

# Load environment variables
load_dotenv()

# Initialize LLM
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in environment variables.")

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)

class AgentState(TypedDict):
    transaction: Dict[str, Any]
    policies: List[str]
    violation_reason: Optional[str]
    is_violation: bool
    investigation_count: int
    spending_history: Optional[str]
    decision: Optional[Literal["SAFE", "VIOLATION", "SUSPICIOUS"]]

def fetch_policies(db: Session) -> List[str]:
    policies = db.query(models.Policy).filter(models.Policy.is_active == True).all()
    return [f"{p.rule_name}: {p.description}" for p in policies]

from sqlalchemy import func

def get_user_spending_history(db: Session, user_id: int) -> str:
    # Fetch all past transactions for this user (excluding current one ideally, but simple query is fine)
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.is_violation == False # Only look at approved history
    ).order_by(models.Transaction.timestamp.desc()).all()
    
    if not transactions:
        return "No previous approved spending history."
    
    total_spent = sum(t.amount for t in transactions)
    count = len(transactions)
    avg_spend = total_spent / count if count > 0 else 0
    
    # Top categories
    categories = {}
    for t in transactions:
        categories[t.category] = categories.get(t.category, 0) + 1
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
    top_cats_str = ", ".join([f"{c} ({n})" for c, n in top_categories])
    
    # Last 3 transactions
    last_3 = transactions[:3]
    last_3_str = "; ".join([f"{t.timestamp.date()}: ${t.amount} at {t.merchant} ({t.category})" for t in last_3])
    
    summary = (
        f"User has {count} approved transactions totaling ${total_spent:.2f}. "
        f"Average spend: ${avg_spend:.2f}. "
        f"Top categories: {top_cats_str}. "
        f"Recent activity: {last_3_str}."
    )
    return summary

def monitor(state: AgentState) -> AgentState:
    print(f"Monitoring transaction: {state['transaction']}")
    return state

def evaluate(state: AgentState) -> AgentState:
    transaction = state['transaction']
    policies = state['policies']
    history = state.get('spending_history', "No history available yet.")
    
    # Construct Prompt
    prompt_template = PromptTemplate.from_template(
        """You are a Visa Security Officer. 
        
        Transaction: {transaction_details} 
        Policies: {active_policy_list} 
        User History: {user_history}
        
        Analyze if this transaction violates ANY policy.
        
        Output one of three decisions:
        - "SAFE": Approve immediately.
        - "VIOLATION": Freeze immediately (clear policy violation).
        - "SUSPICIOUS": If the transaction is weird but not clearly forbidden (e.g., high amount but valid category), and you need more context.
        
        Return ONLY a JSON object: {{"decision": "SAFE" | "VIOLATION" | "SUSPICIOUS", "reason": "short explanation"}}
        """
    )
    
    prompt = prompt_template.format(
        transaction_details=json.dumps(transaction, default=str),
        active_policy_list="\n".join(policies) if policies else "No specific policies defined.",
        user_history=history
    )
    
    print(f"DEBUG: LLM Prompt:\n{prompt}")
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        print(f"DEBUG: LLM Response:\n{content}")
        
        # Clean up potential markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content.strip())
        decision = result.get("decision", "VIOLATION").upper()
        reason = result.get("reason", "No reason provided.")
        
        # Logic for handling decisions
        is_violation = False
        
        if decision == "VIOLATION":
            is_violation = True
        elif decision == "SUSPICIOUS":
            if state['investigation_count'] >= 1:
                # Loop limit reached, fail closed
                decision = "VIOLATION"
                is_violation = True
                reason = f"Suspicious activity confirmed after investigation. {reason}"
            else:
                # Keep as suspicious to trigger investigation
                is_violation = False 
        else:
            # SAFE
            is_violation = False

        return {
            **state,
            "is_violation": is_violation,
            "violation_reason": reason,
            "decision": decision
        }
    except Exception as e:
        print(f"Error in LLM evaluation: {e}")
        return {
            **state,
            "is_violation": True,
            "violation_reason": f"System Error: Security Check Failed ({str(e)})",
            "decision": "VIOLATION"
        }

def investigate(state: AgentState) -> AgentState:
    user_id = state['transaction']['user_id']
    print(f"🕵️ Investigating User {user_id}...")
    
    db = database.SessionLocal()
    try:
        history = get_user_spending_history(db, user_id)
    finally:
        db.close()
    
    return {
        **state,
        "spending_history": history,
        "investigation_count": state['investigation_count'] + 1
    }

def enforce(state: AgentState) -> AgentState:
    if state['is_violation']:
        user_id = state['transaction']['user_id']
        reason = state['violation_reason']
        print(f"Enforcing penalty on user {user_id}: Freezing card. Reason: {reason}")
        
        db = database.SessionLocal()
        try:
            # Freeze User
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                user.card_status = models.CardStatus.FROZEN
                db.add(user)
            
            # Update Transaction with Reason
            trans_id = state['transaction'].get('id')
            if trans_id:
                trans = db.query(models.Transaction).filter(models.Transaction.id == trans_id).first()
                if trans:
                    trans.violation_reason = reason
                    trans.is_violation = True
                    db.add(trans)
            
            db.commit()
        except Exception as e:
            print(f"Error enforcing policy: {e}")
            db.rollback()
        finally:
            db.close()
            
    return state

def decide_next_step(state: AgentState):
    decision = state.get("decision")
    
    if decision == "VIOLATION":
        return "enforce"
    elif decision == "SUSPICIOUS":
        return "investigate"
    else:
        return END

# Build the graph
workflow = StateGraph(AgentState)

workflow.add_node("monitor", monitor)
workflow.add_node("evaluate", evaluate)
workflow.add_node("investigate", investigate)
workflow.add_node("enforce", enforce)

workflow.set_entry_point("monitor")
workflow.add_edge("monitor", "evaluate")

workflow.add_conditional_edges(
    "evaluate",
    decide_next_step,
    {
        "enforce": "enforce",
        "investigate": "investigate",
        END: END
    }
)

workflow.add_edge("investigate", "evaluate") # Loop back
workflow.add_edge("enforce", END)

app = workflow.compile()

def run_transaction_check(transaction_dict: Dict[str, Any]):
    # Fetch policies first to pass into state
    db = database.SessionLocal()
    try:
        policies = fetch_policies(db)
    finally:
        db.close()

    initial_state = AgentState(
        transaction=transaction_dict,
        policies=policies,
        violation_reason=None,
        is_violation=False,
        investigation_count=0,
        spending_history=None,
        decision=None
    )
    
    result = app.invoke(initial_state)
    return result
