# Div-API Portfolio Tracker

A premium, full-stack investment portfolio tracker featuring a robust Flask REST API and a modern glassmorphism frontend. Track your holdings, transactions, and dividends with a sleek, interactive interface.

![Design Preview](https://img.shields.io/badge/Design-Premium_Dark-blueviolet)
![Currency](https://img.shields.io/badge/Currency-PLN_(zł)-green)

## 🌟 Features

- **Modern Dashboard**: High-level overview of your current holdings with real-time value calculation.
- **Dedicated Views**: 
    - **📊 Dashboard**: Portfolio summary and current holdings.
    - **📋 Transactions**: Full history of BUY/SELL actions.
    - **💰 Dividends**: Record and track your passive income.
- **Interactive Tables**: Powered by **DataTables.js**, allowing for seamless sorting, instant searching, and pagination.
- **Multi-Account Support**: Manage multiple brokerage or bank accounts under one profile.
- **Automatic Holding Management**: Recording a transaction automatically updates your holdings and calculates average costs.
- **Premium Aesthetics**: A stunning dark-mode interface with glassmorphism effects, smooth transitions, and a responsive layout.
- **Secure Authentication**: JWT-based login and registration system.

## 🛠 Tech Stack

### Backend
- **Python / Flask**: Core framework.
- **SQLite3**: Relational database for persistent storage.
- **PyJWT**: Secure authentication tokens.
- **bcrypt**: Industrial-grade password hashing.

### Frontend
- **Flask (Frontend App)**: Acts as a web server for the UI.
- **Vanilla CSS**: Custom premium styling and design system.
- **JavaScript / jQuery**: Interactive elements and API integration.
- **DataTables.js**: Advanced data grid features.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.x
- Git

### 2. Setup

1. **Clone the project (Dev branch)**:
   ```bash
   git clone -b dev-dtbl https://github.com/kc59czk/div-api.git
   cd div-api
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python3 -m venv .
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install Flask PyJWT bcrypt
   ```

### 3. Running the Application

This is a two-part application. You need to run both the API and the Frontend.

**A. Start the Backend API (Port 5000)**
```bash
python app.py
```
*Note: The first time you run this, it will initialize the `instance/portfolio.db` database.*

**B. Start the Frontend UI (Port 5050)**
```bash
cd frontend
python app.py
```

### 4. Access
Open your browser and navigate to:
`http://127.0.0.1:5050`

## 📁 Project Structure

```text
div-api/
├── app.py              # Backend API server
├── schema.sql          # Database schema
├── frontend/
│   ├── app.py          # Frontend web server
│   ├── static/         # CSS, JS, and Assets
│   └── templates/      # HTML templates (Jinja2)
└── instance/           # SQLite database location
```

## ⚖️ License

MIT
