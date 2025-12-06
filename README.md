# Apogee: Virtual Crypto Trading Platform

A web-based trading simulator that allows users to buy and sell cryptocurrencies in real-time using play money. The application queries live market data from the Binance API and manages user portfolios using a relational database.

## 🚀 Features
* **Real-time Quotes:** Fetches live prices for ETH, BTC, and other crypto assets via Binance.
* **Portfolio Management:** Tracks cash balance, holdings, and calculates the Grand Total dynamically.
* **Transaction History:** Detailed log of all buy/sell orders with timestamps.
* **Secure Authentication:** Session-based login with password hashing (`werkzeug.security`).
* **Interactive Charts:** Integrated TradingView widgets for symbol visualization.

## 🛠️ Tech Stack
* **Backend:** Python (Flask), SQLite
* **Frontend:** HTML5, Jinja2, Bootstrap (Bootswatch)
* **Data Source:** Binance Public API

## 📂 Project Structure
* `app.py`: Main application controller and route definitions.
* `helpers.py`: Utility functions for API requests and currency formatting.
* `finance.db`: SQLite database (schema provided in `schema.sql`).
* `templates/`: Jinja2 HTML templates.

## ⚡ How to Run
1.  **Clone the repository**
    ```bash
    git clone [https://github.com/sairupeshl/apogee](https://github.com/sairupeshl/apogee)
    cd apogee
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize Database**
    ```bash
    python init_db.py
    ```

4.  **Run the Application**
    ```bash
    flask run
    ```
