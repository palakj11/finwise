# 💸 FinWise AI Pro

FinWise AI Pro is an advanced financial intelligence platform that combines AI-powered analysis, portfolio advisory, and real-time expense tracking into a single interactive dashboard.

---

## 🚀 Features

* 🧠 AI-powered bank statement analyzer (PDF → structured data)
* 📊 Smart financial dashboard with charts & insights
* 🤖 AI-generated spending audit (Gemini API)
* 📈 Wealth advisor with portfolio allocation
* 📡 Live expense tracking via WhatsApp (Twilio webhook)
* 📰 Market sentiment using live news feeds

---

## 🏗️ Project Structure

```
project/
│
├── app.py              # Flask backend
├── index.html          # Frontend dashboard
│
├── uploads/            # Uploaded files (ignored)
└── README.md
```

---

## ⚙️ Installation

```bash
git clone https://github.com/yourusername/finwise-ai.git
cd finwise-ai

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install flask pandas numpy yfinance feedparser google-generativeai twilio
```

---

## 🔐 Environment Variables

Create a `.env` file:

```
SECRET_KEY=your_secret_key
WEBHOOK_SECRET=your_webhook_token
```

---

## ▶️ Run the App

```bash
python app.py
```

Open:

```
http://localhost:5000
```

---

## 🔑 API Key Usage

* Enter your **Google Gemini API key** in the UI
* Key is stored locally in browser (not on server)

---

## 📊 Modules

### 1. Neural Analyzer

* Upload bank PDF
* Extract transactions
* Generate analytics

### 2. Wealth Oracle

* AI portfolio generation
* Real-time stock pricing

### 3. Live Tracker

* WhatsApp-based expense tracking
* Real-time dashboard updates

---

## ⚠️ Security Notice

Do NOT expose:

* Secret keys
* API tokens
* Webhook endpoints without authentication

---

## 📌 Future Improvements

* Secure API key vault (backend instead of frontend)
* User authentication system
* Cloud deployment (AWS / Render)
* Mobile app integration

---

## 👨‍💻 Author

FinWise AI Project
