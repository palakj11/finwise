import os
import re
import json
import time
import pandas as pd
import numpy as np
from google import genai
from google.genai import types
import yfinance as yf
import feedparser
from flask import Flask, render_template, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from io import StringIO

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- GLOBAL DATA ---
bank_transactions = []
live_transactions = []


# --- HELPERS ---
def get_client():
    """Initializes Gemini Client using the key from the request header."""
    localStorage.setItem("gemini_key", k);
    if not api_key: return None
    return genai.Client(api_key=api_key)


def clean_data(obj):
    if isinstance(obj, dict):
        return {k: clean_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_data(v) for v in obj]
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif pd.isna(obj):
        return 0
    return obj


def get_market_news():
    try:
        feed = feedparser.parse(
            "https://news.google.com/rss/search?q=stock+market+india+business&hl=en-IN&gl=IN&ceid=IN:en")
        headlines = [e.title for e in feed.entries[:3]]
        return "; ".join(headlines) if headlines else "Market is Volatile"
    except:
        return "Market is Volatile"


def get_live_price(ticker):
    try:
        if not ticker or ticker == "null": return 0
        if not ticker.endswith('.NS') and not ticker.endswith('.BO'): ticker += '.NS'
        stock = yf.Ticker(ticker)
        price = stock.fast_info.get('last_price', None)
        if not price:
            hist = stock.history(period="1d")
            if not hist.empty: price = hist['Close'].iloc[-1]
        return round(price, 2) if price else 0
    except:
        return 0


def calculate_stats(data_list):
    if not data_list: return clean_data({"income": 0, "expense": 0, "net": 0, "charts": {}})
    df = pd.DataFrame(data_list)
    for c in ['Withdrawal', 'Deposit']:
        if c not in df.columns:
            df[c] = 0.0
        else:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)

    inc = float(df['Deposit'].sum())
    exp = float(df['Withdrawal'].sum())

    cat_series = df[df['Withdrawal'] > 0].groupby('Category')['Withdrawal'].sum()
    trend_exp = df.groupby('Date')['Withdrawal'].sum()
    trend_inc = df.groupby('Date')['Deposit'].sum()

    top_exp_df = df.nlargest(5, 'Withdrawal')
    top_exp = {}
    if not top_exp_df.empty:
        top_exp = dict(zip(top_exp_df['Description'].astype(str).str[:15], top_exp_df['Withdrawal']))

    freq_data = df[df['Withdrawal'] > 0]['Category'].value_counts().to_dict()

    stats = {
        "income": round(inc, 2), "expense": round(exp, 2), "net": round(inc - exp, 2),
        "charts": {
            "cat_data": cat_series.to_dict(), "trend_exp": trend_exp.to_dict(),
            "trend_inc": trend_inc.to_dict(), "top_exp": top_exp, "freq_data": freq_data
        }
    }
    return clean_data(stats)


# ==========================================
#  1. NEURAL ANALYZER (OPTIMIZED FOR TOKENS)
# ==========================================
@app.route('/api/analyze_bank', methods=['POST'])
def analyze_bank():
    try:
        if 'file' not in request.files: raise Exception("No file uploaded")
        f = request.files['file']
        file_bytes = f.read()

        # --- TOKEN SAVING PROMPT ---
        # Highly compressed instructions to save input tokens
        prompt = """
        Parse PDF to CSV. Cols: Date, Description, Category, Withdrawal, Deposit.
        Category Rules:
        - Invest: Zerodha, Groww, Angel
        - Food: Swiggy, Zomato, McD
        - Sub: Netflix, Jio, Prime
        - Transport: Uber, Ola, Fuel
        - Income: Salary, Credit
        - UPI: UPI
        Output strictly raw CSV. No markdown.
        """

        client = get_client()
        if not client: raise Exception("API Key Missing")

        # Using gemini-1.5-flash (More efficient for Free Tier than 2.0)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[types.Part.from_bytes(data=file_bytes, mime_type='application/pdf'), prompt],
            config=types.GenerateContentConfig(max_output_tokens=2000)  # Limits output to prevent quota drain
        )

        text = re.sub(r'```csv|```', '', response.text).strip()
        df = pd.read_csv(StringIO(text)).fillna(0)
        return jsonify(
            {"status": "success", "columns": df.columns.tolist(), "data": clean_data(df.to_dict(orient='records'))})

    except Exception as e:
        print(f"❌ ANALYZER ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/save_transactions', methods=['POST'])
def save_transactions():
    try:
        global bank_transactions
        bank_transactions = clean_data(request.json.get('data'))
        stats = calculate_stats(bank_transactions)
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate_insight', methods=['POST'])
def generate_insight():
    try:
        stats = request.json.get('stats')
        # Ultra-short prompt to save tokens
        prompt = f"Financial Auditor. HTML format. Summary: Inc {stats['income']}, Exp {stats['expense']}. Roast spending in 1 sentence."
        client = get_client()
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=150)
        )
        return jsonify({"insight": response.text})
    except:
        return jsonify({"insight": "<b>⚠️ AI Audit:</b> High spending detected. Cut discretionary costs."})


# ==========================================
#  2. WEALTH ORACLE (OPTIMIZED)
# ==========================================
@app.route('/api/advisor', methods=['POST'])
def advisor():
    data = request.json
    advice = {}

    # Mock Data (Backup)
    mock_response = {
        "market_sentiment": "Volatile (Demo Mode)",
        "benchmark_name": "Nifty 50",
        "benchmark_return": "12.5%",
        "portfolio_alpha": "+4.2%",
        "strategy_note": "Balanced strategy for volatile markets.",
        "portfolio": [
            {"asset": "Nippon India Small Cap", "type": "Mutual Fund", "ticker": "null", "rationale": "High alpha.",
             "allocation_amt": float(data.get('amount')) * 0.4},
            {"asset": "Tata Motors", "type": "Stock", "ticker": "TATAMOTORS.NS", "rationale": "EV Leader.",
             "allocation_amt": float(data.get('amount')) * 0.3},
            {"asset": "HDFC Bank", "type": "Stock", "ticker": "HDFCBANK.NS", "rationale": "Stable Bank.",
             "allocation_amt": float(data.get('amount')) * 0.2},
            {"asset": "Gold Bees ETF", "type": "Gold", "ticker": "GOLDBEES.NS", "rationale": "Safe Haven.",
             "allocation_amt": float(data.get('amount')) * 0.1}
        ]
    }

    try:
        # Compressed prompt
        prompt = f"""
        Wealth Manager Role. Profile: Age {data.get('age')}, Risk {data.get('risk')}, Amt {data.get('amount')}.
        Output JSON: {{
            "market_sentiment": "Bullish/Bearish",
            "benchmark_name": "Nifty 50", "benchmark_return": "12%", "portfolio_alpha": "+4%",
            "strategy_note": "1 sentence strategy.",
            "portfolio": [ {{ "asset": "Name", "type": "Stock/MF", "ticker": "TICKER.NS", "rationale": "Why?", "allocation_amt": 5000 }} ]
        }}
        """

        client = get_client()
        if client:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type='application/json', max_output_tokens=1000)
            )
            advice = json.loads(response.text)
        else:
            advice = mock_response

    except Exception as e:
        print(f"Using Mock Data: {e}")
        advice = mock_response

        # Math Engine
    total_verify = 0
    for item in advice.get('portfolio', []):
        ticker = item.get('ticker')
        live_price = 0
        if ticker and ticker != "null":
            live_price = get_live_price(ticker)
            item['live_price'] = live_price
        else:
            item['live_price'] = "NAV"

        alloc = float(item.get('allocation_amt', 0))
        if live_price > 0:
            item['shares'] = int(alloc / live_price)
        else:
            item['shares'] = "N/A"
        total_verify += alloc

    advice['total_verify'] = round(total_verify, 2)
    return jsonify(advice)


# ==========================================
#  3. LIVE TRACKER
# ==========================================
@app.route('/webhook', methods=['POST'])
def webhook():
    msg = request.values.get('Body', '').lower();
    resp = MessagingResponse();
    d_str = time.strftime("%Y-%m-%d")
    amt = re.search(r'(\d+)', msg)
    if amt:
        val = float(amt.group(1))
        if 'received' in msg:
            live_transactions.append({'Date': d_str, 'Description': 'Income', 'Category': 'Income', 'Withdrawal': 0,
                                      'Deposit': val}); resp.message(f"✅ Credit: {val}")
        else:
            live_transactions.append(
                {'Date': d_str, 'Description': re.sub(r'\d+', '', msg).strip() or "Expense", 'Category': 'Expense',
                 'Withdrawal': val, 'Deposit': 0}); resp.message(f"📉 Debit: {val}")
    return str(resp)


@app.route('/api/tracker_data', methods=['GET'])
def tracker_data():
    return jsonify(
        {"transactions": clean_data(list(reversed(live_transactions))), "stats": calculate_stats(live_transactions)})


@app.route('/')
def home(): return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)T
