import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# A custom class using sqlite3
class Database:
    def __init__(self, path):
        self.path = path

    def execute(self, query, *args):
        # Connect to the database
        conn = sqlite3.connect(self.path)
        
        conn.row_factory = sqlite3.Row 
        
        cur = conn.cursor()
        
        try:
            # Execute the query with the arguments provided
            cur.execute(query, args)
            
            # If it's a SELECT query, return the list of rows
            if query.strip().upper().startswith("SELECT"):
                rows = cur.fetchall()
                conn.close()
                return [dict(row) for row in rows]
            
            # If it's INSERT/UPDATE/DELETE, commit changes
            else:
                conn.commit()
                last_row_id = cur.lastrowid
                conn.close()
                return last_row_id
                
        except Exception as e:
            conn.close()
            print(f"Database Error: {e}")
            raise e

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database
db = Database("finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    
    user_data = db.execute("SELECT cash FROM users WHERE id = ?;", session["user_id"])
    cash = user_data[0]["cash"]
    grand_total = cash
    
    # Create a list of dictionaries to store information about each stock
    records = []

    # For each transaction of the particular stock, add for buy and subtract for sell
    rows = db.execute("""
        SELECT symbol, SUM(CASE WHEN type='buy' THEN shares WHEN type='sell' THEN -shares END) as total_shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        HAVING total_shares > 0;
    """, session["user_id"])

    # For each stock, collect the required information
    for row in rows:
        symbol = row["symbol"]
        shares = row["total_shares"]
        
        stock_info = lookup(symbol)
        
        # Calculate total price of the stock and grand total
        total = shares * stock_info["price"]
        grand_total += total

        # Add the information to records
        records.append({
            "symbol": symbol,
            "shares": shares,
            "price": usd(stock_info["price"]),
            "total": usd(total)
        })

    # Display the information
    return render_template("index.html", cash=usd(cash), grand_total=usd(grand_total), records=records)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # If user reached via GET, display buy.html
    if request.method == "GET":
        return render_template("buy.html")

    # If user reached via POST, i.e., clicks the buy button
    else:

        # Get the input symbol
        symbol = request.form.get("symbol")

        # Ensure symbol is not blank
        if not symbol:
            return apology("Symbol Required", 400)

        # Get the input shares
        shares = request.form.get("shares")

        # Ensure shares is not blank
        if not shares:
            return apology("Shares must not be blank", 400)

        # Ensure shares is a number
        if not shares.isdigit():
            return apology("Shares must be a positve integer", 400)

        # Ensure shares is a positive integer
        shares = int(shares)
        if not shares or shares <= 0 or shares % 1 != 0:
            return apology("Shares must be a positve integer", 400)

        # Get the current price of the stock
        dic = lookup(symbol)

        # Ensure that the symbol is valid
        if not dic:
            return apology("Symbol not found", 400)

        price = dic["price"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?;", session["user_id"])[0]["cash"]

        # Ensure that the user has enough cash
        if price * shares > cash:
            return apology("Not enough money", 400)

        # Update cash
        cash -= price * shares
        db.execute("UPDATE users SET cash = ? WHERE id = ?;", cash, session["user_id"])

        # Update transactions
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, 'buy');",
                   session["user_id"], symbol, shares, price)

        # Redirect the user to the home page
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Get the required information
    rows = db.execute(
        "SELECT symbol, shares, price, type, timestamp FROM transactions WHERE user_id=? ORDER BY timestamp DESC;", session["user_id"])

    # Display history.html
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # If the user reached via GET, display quote.html
    if request.method == "GET":
        return render_template("quote.html")

    # If the user reached via POST, i.e., clicked quote button
    else:

        # Get input symbol
        symbol = request.form.get("symbol")

        # Ensure symbol is not blank
        if not symbol:
            return apology("Symbol required", 400)

        # Get the name and price of the stock
        quote_res = lookup(symbol)

        # Ensure that the symbol is valid
        if not quote_res:
            return apology("Symbol not found", 400)
        name = quote_res["name"]
        price = quote_res["price"]

        # Display the symbol, name and price of the quoted stock
        return render_template("quoted.html", name=name, price=usd(price), symbol=symbol)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # If the user reached via POST, i.e., clicked the register button
    if request.method == "POST":

        # Get inputs from user
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("Must provide username", 400)

        # Ensure password was submitted
        if not password:
            return apology("Must provide password", 400)

        # Ensure password was confirmed
        if not confirmation:
            return apology("Must enter password again for confirmation", 400)

        # Ensure that the password and its confirmation were the same
        if password != confirmation:
            return apology("Password and Confirmation should match", 400)

        # Hash the password
        hashed_password = generate_password_hash(password)

        try:
            # Store the username and password in users table
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                       username, hashed_password)

        # If the username already exists, return an apology
        except:
            return apology("Username already exists", 400)

        else:
            # Log in the user
            session["user_id"] = db.execute(
                "SELECT id FROM users WHERE username=?;", username)[0]["id"]

            # Redirect the user to the home page
            return redirect("/")

    # If the user reached via GET, display register.html
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # If the user reached via POST, i.e., clicked the sell button
    if request.method == "POST":

        # Get input symbol
        symbol = request.form.get("symbol")

        # Ensure that the symbol is not blank
        if not symbol:
            return apology("Select a stock", 400)

        # For each transaction of the particular stock, add for buy and subtract for sell
        rows = db.execute("SELECT SUM( CASE WHEN type='buy' THEN shares WHEN type='sell' THEN -shares END) as total FROM transactions WHERE user_id=? AND symbol=?;",
                                  session["user_id"], symbol)
        stock_shares = rows[0]["total"]

        # If there are no stocks currently in possession
        if stock_shares == 0:
            return apology("Not owned", 400)

        # Get shares input from the user
        shares = request.form.get("shares")

        # Ensure shares is not empty
        if not shares:
            return apology("Enter shares to sell", 400)

        # Ensure shares is a positive integer
        if not shares.isdigit():
            return apology("Shares must be a positive integer", 400)

        shares = int(shares)

        if not shares or shares <= 0 or shares % 1 != 0:
            return apology("Shares must be a positive integer", 400)

        # Ensure that the user has enough stocks to sell
        if shares > stock_shares:
            return apology("You don't own that many shares", 400)

        # Get the price of the stock
        price = lookup(symbol)["price"]

        # Update cash
        cash = db.execute("SELECT cash FROM users WHERE id = ?;", session["user_id"])[0]["cash"]
        cash += price * shares
        db.execute("UPDATE users SET cash = ? WHERE id = ?;", cash, session["user_id"])

        # Update this trnsaction into transactions
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, 'sell');",
                   session["user_id"], symbol, shares, price)

        # Redirect the user to the home page
        return redirect("/")

    # If the user reached via GET, display sell.html
    else:

        # Find stocks currently in possession
        symbols = db.execute(
            "SELECT symbol FROM transactions WHERE user_id=? GROUP BY symbol HAVING SUM( CASE WHEN type='buy' THEN shares WHEN type='sell' THEN -shares END) > 0;", session["user_id"])

        return render_template("sell.html", symbols=symbols)


# Allow users to change their passwords
@app.route("/change_pwd", methods=["GET", "POST"])
@login_required
def change_pwd():
    '''Change password'''

    # If the user reached via GET, i.e., display change_pwd.html
    if request.method == "GET":

        return render_template("change_pwd.html")

    # If the user reached via POST, i.e., clicked the change password button
    else:

        # Get the old, new and confirmation passwords as input from the user
        old_pwd = request.form.get("old_pwd")
        new_pwd = request.form.get("new_pwd")
        confirmation = request.form.get("confirmation")

        # Ensure that the old password isn't blank
        if not old_pwd:
            return apology("Old Password Missing", 400)

        # Ensure that the new password isn't blank
        if not new_pwd:
            return apology("New Password Missing", 400)

        # Ensure confirmation isn't blank
        if not confirmation:
            return apology("Missing Confirmation of the New Password", 400)

        # Ensure that the new password and its confirmation are the same
        if confirmation != new_pwd:
            return apology("Confirmation and New Password should match", 400)

        # Ensure that the old and new passwords are different
        if old_pwd == new_pwd:
            return apology("New and Old Passwords should not be the same", 400)

        # Hash the new password
        hashed_pwd = generate_password_hash(new_pwd)

        # Update the users table with the new hashed password
        db.execute("UPDATE users SET hash=? WHERE id=?;", hashed_pwd, session["user_id"])

        # Redirect user to the home page
        return redirect("/")

@app.route("/reset", methods=["POST"])
@login_required
def reset():
    """Reset the user's cash and portfolio"""
    user_id = session["user_id"]
    
    # Delete all past transactions
    db.execute("DELETE FROM transactions WHERE user_id = ?", user_id)
    
    # Reset cash to 10,000
    db.execute("UPDATE users SET cash = ? WHERE id = ?", 1000000.00, user_id)
    
    flash("Portfolio reset successfully!")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)