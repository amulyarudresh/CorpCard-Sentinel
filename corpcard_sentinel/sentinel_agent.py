import os
import json
from typing import TypedDict, List, Dict, Any, Optional
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
    # Fallback or warning - in a real app this should probably error out
    print("WARNING: GOOGLE_API_KEY not found in environment variables.")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)

class AgentState(TypedDict):
    transaction: Dict[str, Any]
    policies: List[str]
    violation_reason: Optional[str]
    is_violation: bool

def fetch_policies(db: Session) -> List[str]:
    policies = db.query(models.Policy).filter(models.Policy.is_active == True).all()
    return [f"{p.rule_name}: {p.description}" for p in policies]

def monitor(state: AgentState) -> AgentState:
    print(f"Monitoring transaction: {state['transaction']}")
    return state

def evaluate(state: AgentState) -> AgentState:
    transaction = state['transaction']
    policies = state['policies']
    
    # Construct Prompt
    prompt_template = PromptTemplate.from_template(
        """You are a Visa Security Officer. 
        
        Transaction: {transaction_details} 
        Policies: {active_policy_list} 
        
        Analyze if this transaction violates ANY policy. 
        Return ONLY a JSON object: {{"violation": bool, "reason": "short explanation"}}.
        If there are no policies, assume no violation.
        """
    )
    
    prompt = prompt_template.format(
        transaction_details=json.dumps(transaction, default=str),
        active_policy_list="\n".join(policies) if policies else "No specific policies defined."
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
        
        return {
            **state,
            "is_violation": result.get("violation", False),
            "violation_reason": result.get("reason")
        }
    except Exception as e:
        print(f"Error in LLM evaluation: {e}")
        # Fail Closed: Block transaction if security check fails
        return {
            **state,
            "is_violation": True,
            "violation_reason": f"System Error: Security Check Failed ({str(e)})"
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
            # We need to find the transaction again or just assume the caller handles the transaction update?
            # The prompt says: "update the transaction record in the DB with the reason."
            # The transaction ID is in state['transaction']['id']
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

def should_enforce(state: AgentState):
    if state['is_violation']:
        return "enforce"
    return END

# Build the graph
workflow = StateGraph(AgentState)

workflow.add_node("monitor", monitor)
workflow.add_node("evaluate", evaluate)
workflow.add_node("enforce", enforce)

workflow.set_entry_point("monitor")
workflow.add_edge("monitor", "evaluate")
workflow.add_conditional_edges(
    "evaluate",
    should_enforce,
    {
        "enforce": "enforce",
        END: END
    }
)
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
        is_violation=False
    )
    
    result = app.invoke(initial_state)
    return result
