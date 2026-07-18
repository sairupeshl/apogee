import requests

from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    return render_template("apology.html", top=code, bottom=message), code


def login_required(f):
    """
    Decorate routes to require login.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up quote for symbol using Binance API."""

    symbol = symbol.upper().strip()
    url = f"https://api.binance.us/api/v3/ticker/price?symbol={symbol}USDT"
    
    try:
        response = requests.get(url, timeout = 5)

        if response.status_code in [403, 451]:
            print(f"Warning: Binance API blocked in this region for {symbol}.")
            return None
        elif response.status_code == 429:
            print(f"Warning: Binance rate limit exceeded.")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        return {
            "name": symbol, 
            "price": float(data["price"]),
            "symbol": symbol
        }
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"API Connection Error: {e}")
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
