# CorpCard Sentinel 🛡️

CorpCard Sentinel is an AI-powered Corporate Card Fraud Detection System. It uses a **ReAct (Reason + Act)** agentic workflow backed by Google's Gemini LLM to analyze transactions, investigate user history, and prevent fraud before it happens.

## 🧠 Agentic Architecture (ReAct Loop)

The system uses **LangGraph** to orchestrate a sophisticated decision-making process:

1.  **Monitor**: Intercepts the transaction.
2.  **Evaluate**: The LLM analyzes the transaction against active policies and decides:
    *   **SAFE**: Approve immediately.
    *   **VIOLATION**: Block immediately.
    *   **SUSPICIOUS**: Trigger an investigation.
3.  **Investigate**: If suspicious, the agent **queries the database** to fetch the user's spending history (average spend, top categories, recent activity).
4.  **Re-Evaluate**: The LLM re-assesses the transaction with this new context.
5.  **Enforce**: Freezes the card if a violation is confirmed.

## Features

- **Real-time Transaction Simulation**: Simulate transactions and see the agent's thought process.
- **Context-Aware Analysis**: The agent knows if a user "usually buys coffee" or "never spends on Tech".
- **Dynamic Policy Engine**: Create, Update, and Delete policies in natural language (e.g., "No alcohol on weekdays").
- **Card Management**: Automatically freezes cards upon fraud detection.
- **Audit Logs**: View detailed logs including the LLM's reasoning and investigation steps.
- **Fail-Closed Security**: Automatically blocks transactions if the security check fails.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PyMySQL
- **Frontend**: Streamlit
- **AI**: LangChain, LangGraph, Google Gemini API (`gemini-1.5-flash`)
- **Database**: MySQL (Production) / SQLite (Dev)

## Setup Instructions

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd corpcard_sentinel
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Setup**
    Create a `.env` file in the root directory:
    ```env
    GOOGLE_API_KEY=your_api_key_here
    DATABASE_URL=mysql+pymysql://user:pass@host/db_name  # Optional, defaults to local
    LLM_MODEL=gemini-1.5-flash-001
    ```

4.  **Seed the Database**
    Populate the DB with realistic users and policies:
    ```bash
    python -m corpcard_sentinel.seed
    ```

5.  **Run the Backend**
    ```bash
    uvicorn corpcard_sentinel.main:app --reload
    ```
    API: `http://localhost:8000`

6.  **Run the Frontend Dashboard**
    ```bash
    streamlit run corpcard_sentinel/dashboard.py
    ```

## Deployment

### Render (Backend)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn corpcard_sentinel.main:app --host 0.0.0.0 --port 10000`
- **Env Vars**: `GOOGLE_API_KEY`, `DATABASE_URL`, `LLM_MODEL`

### Streamlit Cloud (Frontend)
- **Main File**: `corpcard_sentinel/dashboard.py`
- **Env Vars**: `API_URL` (URL of your Render backend), `GOOGLE_API_KEY` (if needed locally)
