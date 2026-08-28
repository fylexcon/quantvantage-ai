# 📈 QuantVantage AI

**Real-Time Sentiment Analysis & Price Forecasting Engine**

QuantVantage AI is a full-stack, enterprise-grade application that ingests real-time financial news, performs advanced natural language processing to extract market sentiment, and leverages predictive machine learning models to forecast short-term price movements for major assets (AAPL, IONQ, BTC, ETH, SOL).

---

## 🏗️ System Architecture & Data Pipeline

The application is built on a highly decoupled, scalable microservices architecture combining modern web technologies, machine learning inference, and a robust data engineering pipeline.

### Automated News Ingestion (n8n Workflow)

![n8n Workflow Architecture](./n8n-workflow.png)

The core of our real-time data ingestion is powered by a continuous **n8n automation pipeline**:
1. **Triggers:** Initiated via a Schedule Trigger (e.g., hourly cron job) or manual execution.
2. **RSS Read:** Fetches the latest financial news and headlines from global market feeds.
3. **Loop Over Items:** Iterates through the fetched articles for isolated processing.
4. **AI Agent (Google Gemini):** Each article is passed to a Gemini Chat Model equipped with a Structured Output Parser. This forces the LLM to extract the targeted asset ticker, determine the sentiment polarity (Bullish/Bearish/Neutral), and calculate a numerical conviction score (-1.0 to 1.0) in strict JSON format.
5. **HTTP Request:** The structured sentiment payload is POSTed directly to the FastAPI backend on Render.
6. **Wait Node:** Implements a delay loop to respect API rate limits and prevent backend throttling.

---

## 🚀 Key Features

**1. Live Sentiment Analysis**
* Ingests hundreds of articles and financial news sources automatically.
* Uses advanced NLP to assign a sentiment score and categorize market mood.
* Calculates the 24-hour moving average of market sentiment for supported assets.

**2. AI Price Forecasting (14-Day Horizon)**
* PyTorch-based sequence modeling predicts price movements up to 14 days into the future.
* Uses a fusion of historical price momentum, volume, and calculated sentiment scores as input features.
* Generates 1-sigma and 2-sigma confidence intervals to visualize potential volatility.

**3. Real-time Notifications**
* Asynchronous Telegram alerts notify users immediately when an extreme sentiment shift (e.g., highly bullish or bearish signal) is detected on high volume.

**4. Omnichannel Experience**
* **Web Dashboard:** Built with Next.js 15, React, Recharts, and Tailwind CSS. Features a sleek, responsive, glassmorphism dark mode.
* **Mobile App:** Built with React Native & Expo, allowing users to track forecasts and sentiment on the go with pull-to-refresh capabilities.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend (Web)** | Next.js, React, Tailwind CSS, Recharts, SWR, Lucide Icons |
| **Frontend (Mobile)** | React Native, Expo, React Navigation, Gifted Charts |
| **Backend API** | FastAPI, Python, Pydantic, Uvicorn |
| **Machine Learning** | PyTorch, Scikit-learn, Pandas |
| **Database & Auth** | Supabase (PostgreSQL), pgvector, Row Level Security (RLS) |
| **Automation** | n8n, Google Gemini LLM API |
| **Hosting & CI/CD** | Vercel (Web), Render (API), GitHub Actions |

---

## 📂 Project Structure

```text
quantvantage-ai/
├── apps/
│   ├── web/                # Next.js web application
│   ├── mobile/             # Expo React Native mobile application
│   └── api/                # FastAPI backend & PyTorch inference
│       ├── models/         # Pydantic schemas & PyTorch model definitions
│       ├── routers/        # API endpoints (sentiment, predictions)
│       └── utils/          # Telegram alerts, helpers
├── README.md
└── package.json
