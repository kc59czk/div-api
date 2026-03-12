# Dividend Tracker API (div-api)

A REST API built with Flask for tracking personal investment portfolios and dividend income. It features JWT-based authentication, account management, and database support via SQLite.

## Features

- **User Authentication:** Registration and login using securely hashed passwords (`bcrypt`) and JWT tokens.
- **Account Management:** Users can manage multiple investment accounts.
- **Holdings Tracking:** Record and track stock holdings (company symbol / "spółka", purchase date, quantity, price) across accounts.
- **Dividend Tracking:** Record received dividends per account and per company.
- **Data Isolation:** All portfolio data (accounts, holdings, dividends) is securely isolated per user.

## Tech Stack

- **Python 3**
- **Flask** - Web Framework
- **SQLite3** - Relational Database
- **PyJWT** - Authentication (JSON Web Tokens)
- **bcrypt** - Password Hashing

## Installation & Setup

1. **Navigate to the project directory:**
   ```bash
   cd path/to/div-api
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the required dependencies:**
   *(Ensure you have Flask, PyJWT, and bcrypt installed)*
   ```bash
   pip install Flask PyJWT bcrypt
   ```

4. **Initialize the database:**
   The application uses an SQLite database stored in `instance/portfolio.db`. The easiest way to initialize it is to temporarily uncomment the `init_db()` line at the bottom of `app.py`:
   ```python
   if __name__ == "__main__":
       init_db()  # <-- uncomment ONLY the first time
       app.run(debug=True)
   ```
   After running it once, you can comment it back out.

5. **Run the application:**
   ```bash
   python3 app.py
   ```
   The API will be available at `http://127.0.0.1:5000`.

## API Endpoints Reference

### Authentication

*The endpoints below are public.*

* `POST /auth/register`
  * Body: `{"username": "...", "email": "...", "password": "..."}`
  * Description: Registers a new user.
* `POST /auth/login`
  * Body: `{"username": "...", "password": "..."}`
  * Description: Authenticates the user and returns an `access_token`.

---

**Note:** All of the following endpoints require an `Authorization` header containing the valid JWT token:
```
Authorization: Bearer <your_access_token>
```

### Accounts

* `GET /accounts` 
  * Description: Retrieve a list of all accounts for the authenticated user.
* `POST /accounts` 
  * Body: `{"name": "Broker A"}`
  * Description: Create a new account under the authenticated user.
* `DELETE /accounts/<int:account_id>`
  * Description: Delete a specific account.

### Holdings

* `GET /holdings` 
  * URL Parameters (optional): `?account_id=<id>&spolka=<symbol>`
  * Description: List holdings. Filters can be applied by account ID or company.
* `POST /holdings`
  * Body: `{"account_id": 1, "spolka": "AAPL", "data": "2023-01-01", "quantity": 10, "price": 150.0}`
  * Description: Record a new stock holding directly (Note: consider using `/transactions` instead to automatically update holdings).
* `DELETE /holdings/<int:holding_id>`
  * Description: Delete a specific holding.

### Transactions

* `GET /transactions`
  * URL Parameters (optional): `?account_id=<id>&spolka=<symbol>`
  * Description: List recorded transactions. Filters can be applied by account ID or company.
* `POST /transactions`
  * Body: `{"account_id": 1, "spolka": "AAPL", "type": "BUY", "data": "2023-01-01", "quantity": 10, "price": 150.0}`
  * Description: Record a transaction (`BUY` or `SELL`). This will automatically create or update the corresponding entry in the `holdings` table.
* `DELETE /transactions/<int:transaction_id>`
  * Description: Delete a specific transaction. This will attempt to reverse the transaction's effect on the `holdings` table.

### Dividends

* `GET /dividends`
  * URL Parameters (optional): `?account_id=<id>&spolka=<symbol>`
  * Description: List recorded dividends. Filters can be applied by account ID or company.
* `POST /dividends`
  * Body: `{"account_id": 1, "spolka": "AAPL", "data": "2023-06-01", "amount": 15.50}`
  * Description: Record a new dividend payout.
* `DELETE /dividends/<int:dividend_id>`
  * Description: Delete a specific dividend record.

## Configuration

In a production environment, be sure to set the `SECRET_KEY` environment variable to a secure, random string (rather than using the hardcoded default).

```bash
export SECRET_KEY="your_super_secure_random_string"
```
