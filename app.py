# app.py
import sqlite3
import jwt
import bcrypt
import datetime
from functools import wraps
from flask import Flask, request, jsonify, g
import os

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-prod")
DATABASE = os.path.join("instance", "portfolio.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Ensure instance folder exists
os.makedirs("instance", exist_ok=True)

# ----------------------------
# Database helpers
# ----------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # enables dict-like access
    return g.db

@app.teardown_appcontext
def close_db(e):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open("schema.sql", "r") as f:
            db.executescript(f.read())
        db.commit()

# Call once to initialize (you can comment out after first run)
# init_db()

# ----------------------------
# Auth helpers
# ----------------------------

def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return jsonify({"error": "Token missing or invalid format"}), 401
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

def get_user_accounts():
    """Helper: get list of account IDs owned by current user"""
    cur = get_db().execute(
        "SELECT id FROM accounts WHERE user_id = ?", (g.user_id,)
    )
    return [row["id"] for row in cur.fetchall()]

# ----------------------------
# Routes
# ----------------------------

# ---- AUTH ----

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"error": "Missing fields"}), 400

    db = get_db()
    try:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hashed.decode("utf-8")),
        )
        db.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return jsonify({"error": "Username already taken"}), 409
        if "email" in str(e):
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": "Registration failed"}), 400

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not all([username, password]):
        return jsonify({"error": "Missing credentials"}), 400

    db = get_db()
    cur = db.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cur.fetchone()

    if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        token = generate_token(user["id"])
        return jsonify({"access_token": token, "user_id": user["id"]}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# ---- ACCOUNTS ----

@app.route("/accounts", methods=["GET"])
@token_required
def get_accounts():
    cur = get_db().execute("SELECT id, name FROM accounts WHERE user_id = ?", (g.user_id,))
    accounts = [dict(row) for row in cur.fetchall()]
    return jsonify(accounts), 200

@app.route("/accounts", methods=["POST"])
@token_required
def create_account():
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Account name required"}), 400

    db = get_db()
    try:
        db.execute("INSERT INTO accounts (user_id, name) VALUES (?, ?)", (g.user_id, name))
        db.commit()
        cur = db.execute("SELECT id, name FROM accounts WHERE rowid = last_insert_rowid()")
        account = dict(cur.fetchone())
        return jsonify(account), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Account name already exists for this user"}), 409

@app.route("/accounts/<int:account_id>", methods=["DELETE"])
@token_required
def delete_account(account_id):
    db = get_db()
    cur = db.execute("SELECT user_id FROM accounts WHERE id = ?", (account_id,))
    acc = cur.fetchone()
    if not acc or acc["user_id"] != g.user_id:
        return jsonify({"error": "Account not found or access denied"}), 404

    db.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    db.commit()
    return "", 204

# ---- HOLDINGS ----

@app.route("/holdings", methods=["GET"])
@token_required
def get_holdings():
    account_id = request.args.get("account_id", type=int)
    spolka = request.args.get("spolka")

    query = """
        SELECT h.* FROM holdings h
        JOIN accounts a ON h.account_id = a.id
        WHERE a.user_id = ?
    """
    params = [g.user_id]

    if account_id:
        query += " AND h.account_id = ?"
        params.append(account_id)
    if spolka:
        query += " AND h.spolka = ?"
        params.append(spolka)

    cur = get_db().execute(query, params)
    holdings = [dict(row) for row in cur.fetchall()]
    return jsonify(holdings), 200

@app.route("/holdings", methods=["POST"])
@token_required
def create_holding():
    data = request.get_json()
    account_id = data.get("account_id")
    spolka = data.get("spolka")
    data_date = data.get("data")
    quantity = data.get("quantity")
    price = data.get("price")

    if not all([account_id, spolka, data_date, quantity, price]):
        return jsonify({"error": "Missing required fields"}), 400
    if quantity <= 0 or price <= 0:
        return jsonify({"error": "Quantity and price must be positive"}), 400

    # Verify account belongs to user
    db = get_db()
    cur = db.execute("SELECT user_id FROM accounts WHERE id = ?", (account_id,))
    acc = cur.fetchone()
    if not acc or acc["user_id"] != g.user_id:
        return jsonify({"error": "Invalid account ID"}), 403

    db.execute(
        "INSERT INTO holdings (account_id, spolka, data, quantity, price) VALUES (?, ?, ?, ?, ?)",
        (account_id, spolka, data_date, quantity, price)
    )
    db.commit()
    cur = db.execute("SELECT * FROM holdings WHERE rowid = last_insert_rowid()")
    holding = dict(cur.fetchone())
    return jsonify(holding), 201

@app.route("/holdings/<int:holding_id>", methods=["DELETE"])
@token_required
def delete_holding(holding_id):
    db = get_db()
    cur = db.execute("""
        SELECT h.id FROM holdings h
        JOIN accounts a ON h.account_id = a.id
        WHERE h.id = ? AND a.user_id = ?
    """, (holding_id, g.user_id))
    if not cur.fetchone():
        return jsonify({"error": "Holding not found or access denied"}), 404

    db.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
    db.commit()
    return "", 204

# ---- TRANSACTIONS ----

@app.route("/transactions", methods=["GET"])
@token_required
def get_transactions():
    account_id = request.args.get("account_id", type=int)
    spolka = request.args.get("spolka")

    query = """
        SELECT t.* FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = ?
    """
    params = [g.user_id]

    if account_id:
        query += " AND t.account_id = ?"
        params.append(account_id)
    if spolka:
        query += " AND t.spolka = ?"
        params.append(spolka)

    cur = get_db().execute(query, params)
    transactions = [dict(row) for row in cur.fetchall()]
    return jsonify(transactions), 200

@app.route("/transactions", methods=["POST"])
@token_required
def create_transaction():
    data = request.get_json()
    account_id = data.get("account_id")
    spolka = data.get("spolka")
    type = data.get("type")
    data_date = data.get("data")
    quantity = data.get("quantity")
    price = data.get("price")

    if not all([account_id, spolka, type, data_date, quantity, price]):
        return jsonify({"error": "Missing required fields"}), 400
    if type not in ["BUY", "SELL"]:
        return jsonify({"error": "Type must be BUY or SELL"}), 400
    if quantity <= 0 or price <= 0:
        return jsonify({"error": "Quantity and price must be positive"}), 400

    db = get_db()
    
    # Verify account belongs to user
    cur = db.execute("SELECT user_id FROM accounts WHERE id = ?", (account_id,))
    acc = cur.fetchone()
    if not acc or acc["user_id"] != g.user_id:
        return jsonify({"error": "Invalid account ID"}), 403

    # Check current holding
    cur = db.execute(
        "SELECT id, quantity, price FROM holdings WHERE account_id = ? AND spolka = ?",
        (account_id, spolka)
    )
    holding = cur.fetchone()

    if type == "SELL":
        if not holding or holding["quantity"] < quantity:
            return jsonify({"error": "Insufficient quantity in holdings to sell"}), 400
            
    # Insert Transaction
    db.execute(
        "INSERT INTO transactions (account_id, spolka, type, data, quantity, price) VALUES (?, ?, ?, ?, ?, ?)",
        (account_id, spolka, type, data_date, quantity, price)
    )
    
    # Update Holdings
    if type == "BUY":
        if holding:
            # Update existing holding
            # Calculate new average price
            total_cost = (holding["quantity"] * holding["price"]) + (quantity * price)
            new_quantity = holding["quantity"] + quantity
            new_price = total_cost / new_quantity
            db.execute(
                "UPDATE holdings SET quantity = ?, price = ? WHERE id = ?",
                (new_quantity, new_price, holding["id"])
            )
        else:
            # Create new holding
            db.execute(
                "INSERT INTO holdings (account_id, spolka, data, quantity, price) VALUES (?, ?, ?, ?, ?)",
                (account_id, spolka, data_date, quantity, price)
            )
    elif type == "SELL":
        new_quantity = holding["quantity"] - quantity
        if new_quantity == 0:
            db.execute("DELETE FROM holdings WHERE id = ?", (holding["id"],))
        else:
            # Selling doesn't typically change the average cost basis (price per share) for remaining shares
            db.execute(
                "UPDATE holdings SET quantity = ? WHERE id = ?",
                (new_quantity, holding["id"])
            )
            
    db.commit()
    
    cur = db.execute("SELECT * FROM transactions WHERE rowid = last_insert_rowid()")
    transaction = dict(cur.fetchone())
    return jsonify(transaction), 201

@app.route("/transactions/<int:transaction_id>", methods=["DELETE"])
@token_required
def delete_transaction(transaction_id):
    db = get_db()
    
    # Verify transaction belongs to user's account and get details
    cur = db.execute("""
        SELECT t.* FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE t.id = ? AND a.user_id = ?
    """, (transaction_id, g.user_id))
    transaction = cur.fetchone()
    
    if not transaction:
        return jsonify({"error": "Transaction not found or access denied"}), 404

    account_id = transaction["account_id"]
    spolka = transaction["spolka"]
    type = transaction["type"]
    quantity = transaction["quantity"]
    price = transaction["price"]
    
    # Get current holding
    cur = db.execute(
        "SELECT id, quantity, price FROM holdings WHERE account_id = ? AND spolka = ?",
        (account_id, spolka)
    )
    holding = cur.fetchone()
    
    if type == "BUY":
        # Reversing a BUY is equivalent to a SELL without constraints
        if not holding or holding["quantity"] < quantity:
            return jsonify({"error": "Cannot delete BUY transaction: Holdings quantity too low (may have been sold)"}), 400
            
        new_quantity = holding["quantity"] - quantity
        if new_quantity == 0:
            db.execute("DELETE FROM holdings WHERE id = ?", (holding["id"],))
        else:
            # Recalculate original average price roughly (can be inaccurate if multiple buys/sells occurred)
            # The most accurate way requires replaying all transactions, but we do a best-effort reversal here
            total_current_value = holding["quantity"] * holding["price"]
            removed_value = quantity * price
            
            # Prevent division by zero or negative values
            if total_current_value > removed_value and new_quantity > 0:
                 new_price = (total_current_value - removed_value) / new_quantity
                 db.execute(
                     "UPDATE holdings SET quantity = ?, price = ? WHERE id = ?",
                     (new_quantity, new_price, holding["id"])
                 )
            else:
                 # Fallback: just reduce quantity, leave average price alone
                 db.execute(
                     "UPDATE holdings SET quantity = ? WHERE id = ?",
                     (new_quantity, holding["id"])
                 )
    elif type == "SELL":
        # Reversing a SELL is equivalent to adding the holding back
        if holding:
             # Typically, a reversed sell just adds the quantity back at the current average price,
             # though strictly speaking it restores the previous average price. For simplicity, we just add quantity.
             new_quantity = holding["quantity"] + quantity
             db.execute(
                 "UPDATE holdings SET quantity = ? WHERE id = ?",
                 (new_quantity, holding["id"])
             )
        else:
             # The holding was deleted entirely by the sell, we need to create it again.
             # We use the sell price as the cost basis, though the original cost basis might have been different.
             db.execute(
                 "INSERT INTO holdings (account_id, spolka, data, quantity, price) VALUES (?, ?, ?, ?, ?)",
                 (account_id, spolka, transaction["data"], quantity, price)
             )

    db.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    db.commit()
    return "", 204

# ---- DIVIDENDS ----

@app.route("/dividends", methods=["GET"])
@token_required
def get_dividends():
    account_id = request.args.get("account_id", type=int)
    spolka = request.args.get("spolka")

    query = """
        SELECT d.* FROM dividends d
        JOIN accounts a ON d.account_id = a.id
        WHERE a.user_id = ?
    """
    params = [g.user_id]

    if account_id:
        query += " AND d.account_id = ?"
        params.append(account_id)
    if spolka:
        query += " AND d.spolka = ?"
        params.append(spolka)

    cur = get_db().execute(query, params)
    dividends = [dict(row) for row in cur.fetchall()]
    return jsonify(dividends), 200

@app.route("/dividends", methods=["POST"])
@token_required
def create_dividend():
    data = request.get_json()
    account_id = data.get("account_id")
    spolka = data.get("spolka")
    data_date = data.get("data")
    amount = data.get("amount")

    if not all([account_id, spolka, data_date, amount]):
        return jsonify({"error": "Missing required fields"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    db = get_db()
    cur = db.execute("SELECT user_id FROM accounts WHERE id = ?", (account_id,))
    acc = cur.fetchone()
    if not acc or acc["user_id"] != g.user_id:
        return jsonify({"error": "Invalid account ID"}), 403

    db.execute(
        "INSERT INTO dividends (account_id, spolka, data, amount) VALUES (?, ?, ?, ?)",
        (account_id, spolka, data_date, amount)
    )
    db.commit()
    cur = db.execute("SELECT * FROM dividends WHERE rowid = last_insert_rowid()")
    dividend = dict(cur.fetchone())
    return jsonify(dividend), 201

@app.route("/dividends/<int:dividend_id>", methods=["DELETE"])
@token_required
def delete_dividend(dividend_id):
    db = get_db()
    cur = db.execute("""
        SELECT d.id FROM dividends d
        JOIN accounts a ON d.account_id = a.id
        WHERE d.id = ? AND a.user_id = ?
    """, (dividend_id, g.user_id))
    if not cur.fetchone():
        return jsonify({"error": "Dividend not found or access denied"}), 404

    db.execute("DELETE FROM dividends WHERE id = ?", (dividend_id,))
    db.commit()
    return "", 204

# ----------------------------
# Run
# ----------------------------

if __name__ == "__main__":
    # Uncomment the next line ONLY the first time to create tables
    # init_db()
    app.run(debug=True)
