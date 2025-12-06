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
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return {
            "name": symbol, 
            "price": float(data["price"]),
            "symbol": symbol
        }
    except (requests.RequestException, ValueError, KeyError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"