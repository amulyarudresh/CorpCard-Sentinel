# CorpCard Sentinel 🛡️

CorpCard Sentinel is an AI-powered Corporate Card Fraud Detection System. It uses a real-time policy engine backed by Google's Gemini LLM to analyze transactions and prevent fraud before it happens.

## Features

- **Real-time Transaction Simulation**: Simulate transactions and see immediate feedback.
- **AI-Powered Analysis**: Uses Gemini 1.5 Flash to analyze transactions against complex natural language policies.
- **Policy Management**: Create, Update, and Delete policies dynamically.
- **Card Management**: Freeze/Unfreeze user cards.
- **Audit Logs**: View a detailed history of all transactions with AI analysis.
- **Fail-Closed Security**: Automatically blocks transactions if the security check fails.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PyMySQL
- **Frontend**: Streamlit
- **AI**: LangChain, LangGraph, Google Gemini API
- **Database**: MySQL (or SQLite for demo)

## Setup Instructions

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd corpcard_sentinel
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r corpcard_sentinel/requirements.txt
    ```

3.  **Environment Setup**
    Create a `.env` file in the root directory and add your Google API Key:
    ```
    GOOGLE_API_KEY=your_api_key_here
    ```

4.  **Run the Backend**
    ```bash
    uvicorn corpcard_sentinel.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

5.  **Run the Frontend Dashboard**
    Open a new terminal and run:
    ```bash
    streamlit run corpcard_sentinel/dashboard.py
    ```
    The dashboard will open in your browser.

## Usage

1.  **Seed Data**: Run `python -m corpcard_sentinel.seed` to populate the database with initial users and policies.
2.  **Simulate**: Go to the "Live Simulation" tab to test transactions.
3.  **Manage**: Use "Policy Control" to add new rules like "No Gambling".
