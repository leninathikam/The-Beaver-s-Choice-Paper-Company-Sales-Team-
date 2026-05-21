import pandas as pd
import numpy as np
import os
import time
import json
import re
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional
from sqlalchemy import create_engine, Engine
from smolagents import ToolCallingAgent, OpenAIServerModel, tool

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################

# --- Vocareum OpenAI configuration (see Udacity Cloud Resources for your key) ---
dotenv.load_dotenv()

model = None


def _get_model() -> OpenAIServerModel:
    global model
    if model is not None:
        return model
    api_key = os.getenv("UDACITY_OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "UDACITY_OPENAI_API_KEY not found. Create a .env file in this folder:\n"
            "  UDACITY_OPENAI_API_KEY=voc-your-key-here\n"
            "Get your Vocareum key from Cloud Resources in the Udacity workspace."
        )
    model = OpenAIServerModel(
        model_id="gpt-4o-mini",
        api_base="https://openai.vocareum.com/v1",
        api_key=api_key,
    )
    return model

# Shared context for the active customer request (set by orchestrator before each run)
_request_context: Dict[str, str] = {"as_of_date": "2025-01-01", "customer_deadline": ""}


def _set_request_context(as_of_date: str, customer_deadline: str = "") -> None:
    _request_context["as_of_date"] = as_of_date.split("T")[0]
    _request_context["customer_deadline"] = customer_deadline


def _extract_deadline(text: str) -> str:
    """Pull the first delivery deadline from free-form customer text."""
    patterns = [
        r"deliver(?:ed|y)?\s+by\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"needed\s+by\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"by\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return datetime.strptime(match.group(1).replace(",", ""), "%B %d %Y").strftime("%Y-%m-%d")
            except ValueError:
                continue
    return ""


def _resolve_item_name(name: str) -> Optional[str]:
    """Map customer phrasing to exact catalog item names."""
    catalog = {item["item_name"].lower(): item["item_name"] for item in paper_supplies}
    key = name.strip().lower()
    if key in catalog:
        return catalog[key]

    aliases = {
        "a4 glossy paper": "Glossy paper",
        "glossy a4 paper": "Glossy paper",
        "a3 glossy paper": "Glossy paper",
        "a4 matte paper": "Matte paper",
        "a3 matte paper": "Matte paper",
        "a4 matte": "Matte paper",
        "matte a3 paper": "Matte paper",
        "heavy cardstock": "Heavyweight paper",
        "heavyweight cardstock": "Heavyweight paper",
        "cardstock": "Cardstock",
        "colored cardstock": "Colored paper",
        "recycled cardstock": "Recycled paper",
        "a4 paper": "A4 paper",
        "a4 printing paper": "A4 paper",
        "a4 printer paper": "A4 paper",
        "a4 white paper": "A4 paper",
        "a4 white printer paper": "A4 paper",
        "standard printer paper": "Standard copy paper",
        "standard copy paper": "Standard copy paper",
        "printer paper": "Standard copy paper",
        "white printer paper": "Standard copy paper",
        "printing paper": "Standard copy paper",
        "construction paper": "Construction paper",
        "colorful construction paper": "Construction paper",
        "poster paper": "Poster paper",
        "colorful poster paper": "Poster paper",
        "poster board": "Large poster paper (24x36 inches)",
        "poster boards": "Large poster paper (24x36 inches)",
        "streamers": "Party streamers",
        "washi tape": "Decorative adhesive tape (washi tape)",
        "decorative washi tape": "Decorative adhesive tape (washi tape)",
        "paper napkins": "Paper napkins",
        "table napkins": "Paper napkins",
        "paper cups": "Paper cups",
        "disposable cups": "Disposable cups",
        "biodegradable paper cups": "Paper cups",
        "paper plates": "Paper plates",
        "biodegradable paper plates": "Paper plates",
        "envelopes": "Envelopes",
        "kraft paper envelopes": "Envelopes",
        "recycled kraft paper envelopes": "Envelopes",
        "flyers": "Flyers",
        "posters": "Poster paper",
        "tickets": "Flyers",
        "glossy paper": "Glossy paper",
        "high-quality glossy paper": "Glossy paper",
        "recycled paper": "Recycled paper",
        "eco-friendly paper": "Eco-friendly paper",
        "letter-sized paper": "Letter-sized paper",
        "letterhead paper": "Letterhead paper",
        "photo paper": "Photo paper",
        "glossy photo paper": "Photo paper",
        "sticky notes": "Sticky notes",
        "invitation cards": "Invitation cards",
        "presentation folders": "Presentation folders",
        "table covers": "Table covers",
        "crepe paper": "Crepe paper",
        "glitter paper": "Glitter paper",
        "banner paper": "Banner paper",
        "kraft paper": "Kraft paper",
        "legal-size paper": "Legal-size paper",
        "uncoated paper": "Uncoated paper",
        "butcher paper": "Butcher paper",
        "bright-colored paper": "Bright-colored paper",
        "patterned paper": "Patterned paper",
        "100 lb cover stock": "100 lb cover stock",
        "80 lb text paper": "80 lb text paper",
        "250 gsm cardstock": "250 gsm cardstock",
        "220 gsm poster paper": "220 gsm poster paper",
    }
    if key in aliases:
        return aliases[key]

    for alias, canonical in aliases.items():
        if alias in key or key in alias:
            return canonical
    for item_lower, item_name in catalog.items():
        if item_lower in key or key in item_lower:
            return item_name
    return None


def _parse_line_items(items_json: str) -> List[Dict]:
    items = json.loads(items_json)
    parsed = []
    for entry in items:
        raw_name = entry.get("item_name") or entry.get("name", "")
        qty = int(entry.get("quantity") or entry.get("units", 0))
        resolved = _resolve_item_name(raw_name)
        if not resolved:
            parsed.append({"item_name": raw_name, "quantity": qty, "resolved": False})
        else:
            parsed.append({"item_name": resolved, "quantity": qty, "resolved": True})
    return parsed


def _bulk_discount_rate(total_units: int) -> float:
    if total_units >= 5000:
        return 0.15
    if total_units >= 1000:
        return 0.10
    if total_units >= 500:
        return 0.08
    if total_units >= 200:
        return 0.05
    return 0.0


def _get_unit_price(item_name: str) -> float:
    for item in paper_supplies:
        if item["item_name"] == item_name:
            return item["unit_price"]
    inv = pd.read_sql(
        "SELECT unit_price FROM inventory WHERE item_name = :name",
        db_engine,
        params={"name": item_name},
    )
    if not inv.empty:
        return float(inv.iloc[0]["unit_price"])
    return 0.0


# --- Tools for inventory agent ---

@tool
def list_catalog_items() -> str:
    """Return all paper products the company sells with unit prices."""
    lines = [f"- {item['item_name']}: ${item['unit_price']:.2f} ({item['category']})" for item in paper_supplies]
    return "Available catalog items:\n" + "\n".join(lines)


@tool
def get_inventory_snapshot(as_of_date: str) -> str:
    """Return current stock levels for all in-stock items as of a given date.

    Args:
        as_of_date: Inventory cutoff date in YYYY-MM-DD format.
    """
    stock = get_all_inventory(as_of_date)
    if not stock:
        return f"No inventory on hand as of {as_of_date}."
    lines = [f"- {name}: {qty} units" for name, qty in sorted(stock.items())]
    return f"Inventory as of {as_of_date}:\n" + "\n".join(lines)


@tool
def check_items_availability(items_json: str, as_of_date: str) -> str:
    """Check whether requested items are in stock.

    Args:
        items_json: JSON list like [{"item_name":"A4 paper","quantity":200}].
        as_of_date: Date for stock lookup in YYYY-MM-DD format.
    """
    parsed = _parse_line_items(items_json)
    results = []
    reorder_needed = []
    for entry in parsed:
        if not entry["resolved"]:
            results.append(f"UNAVAILABLE: '{entry['item_name']}' is not in our catalog.")
            continue
        stock_df = get_stock_level(entry["item_name"], as_of_date)
        current = int(stock_df["current_stock"].iloc[0])
        needed = entry["quantity"]
        if current >= needed:
            results.append(f"OK: {entry['item_name']} — need {needed}, have {current}")
        else:
            shortfall = needed - current
            results.append(
                f"LOW: {entry['item_name']} — need {needed}, have {current}, short {shortfall}"
            )
            reorder_needed.append({"item_name": entry["item_name"], "shortfall": shortfall, "needed": needed})
    summary = "\n".join(results)
    if reorder_needed:
        summary += "\n\nReorder recommended for: " + ", ".join(r["item_name"] for r in reorder_needed)
    return summary


@tool
def place_restock_order(item_name: str, quantity: int, as_of_date: str) -> str:
    """Place a supplier stock order when inventory is low.

    Args:
        item_name: Catalog item name to reorder.
        quantity: Number of units to order from the supplier.
        as_of_date: Transaction date in YYYY-MM-DD format.
    """
    resolved = _resolve_item_name(item_name) or item_name
    unit_price = _get_unit_price(resolved)
    if unit_price == 0:
        return f"Cannot reorder '{item_name}': item not found in catalog."

    order_qty = max(quantity, 100)
    total_cost = order_qty * unit_price
    cash = get_cash_balance(as_of_date)
    if cash < total_cost:
        return (
            f"Insufficient cash to reorder {resolved}. Need ${total_cost:.2f}, have ${cash:.2f}."
        )

    delivery = get_supplier_delivery_date(as_of_date, order_qty)
    create_transaction(resolved, "stock_orders", order_qty, total_cost, as_of_date)
    return (
        f"Restock order placed: {order_qty} units of {resolved} "
        f"(${total_cost:.2f}). Supplier delivery expected by {delivery}."
    )


@tool
def auto_restock_if_needed(items_json: str, as_of_date: str) -> str:
    """Automatically reorder items below minimum stock or insufficient for the order.

    Args:
        items_json: JSON list of requested items with quantities.
        as_of_date: Transaction date in YYYY-MM-DD format.
    """
    parsed = _parse_line_items(items_json)
    actions = []
    for entry in parsed:
        if not entry["resolved"]:
            continue
        item_name = entry["item_name"]
        stock_df = get_stock_level(item_name, as_of_date)
        current = int(stock_df["current_stock"].iloc[0])
        needed = entry["quantity"]

        inv_row = pd.read_sql(
            "SELECT min_stock_level FROM inventory WHERE item_name = :name",
            db_engine,
            params={"name": item_name},
        )
        min_level = int(inv_row.iloc[0]["min_stock_level"]) if not inv_row.empty else 100

        if current >= needed and current >= min_level:
            actions.append(f"No restock needed for {item_name} (stock: {current}).")
            continue

        reorder_qty = max(needed - current, min_level * 2)
        result = place_restock_order(item_name, reorder_qty, as_of_date)
        actions.append(result)
    return "\n".join(actions) if actions else "All items sufficiently stocked."


# --- Tools for quoting agent ---

@tool
def search_historical_quotes(search_terms: str) -> str:
    """Search past quotes by keywords to inform pricing strategy.

    Args:
        search_terms: Comma-separated keywords to search in quote history.
    """
    terms = [t.strip() for t in search_terms.split(",") if t.strip()]
    if not terms:
        terms = ["paper"]
    matches = search_quote_history(terms, limit=5)
    if not matches:
        return "No matching historical quotes found."
    lines = []
    for q in matches:
        lines.append(
            f"- ${q['total_amount']:.0f} | {q['job_type']}/{q['event_type']} | "
            f"{q['quote_explanation'][:120]}..."
        )
    return "Historical quotes:\n" + "\n".join(lines)


@tool
def calculate_quote(items_json: str, as_of_date: str) -> str:
    """Calculate a price quote with bulk discounts.

    Args:
        items_json: JSON list of items with item_name and quantity fields.
        as_of_date: Quote date in YYYY-MM-DD format.
    """
    parsed = _parse_line_items(items_json)
    lines = []
    subtotal = 0.0
    total_units = 0
    unavailable = []

    for entry in parsed:
        if not entry["resolved"]:
            unavailable.append(entry["item_name"])
            continue
        price = _get_unit_price(entry["item_name"])
        line_total = price * entry["quantity"]
        subtotal += line_total
        total_units += entry["quantity"]
        lines.append(
            f"  {entry['item_name']}: {entry['quantity']} x ${price:.2f} = ${line_total:.2f}"
        )

    discount_rate = _bulk_discount_rate(total_units)
    discount_amount = subtotal * discount_rate
    total = round(subtotal - discount_amount)

    result = f"Quote breakdown (as of {as_of_date}):\n" + "\n".join(lines)
    result += f"\n  Subtotal: ${subtotal:.2f}"
    if discount_rate > 0:
        result += f"\n  Bulk discount ({discount_rate:.0%}): -${discount_amount:.2f}"
    result += f"\n  TOTAL: ${total:.2f}"
    if unavailable:
        result += f"\n  NOTE: These items are NOT in our catalog: {', '.join(unavailable)}"
    return result


@tool
def get_pricing_for_item(item_name: str) -> str:
    """Look up the unit price for a specific catalog item.

    Args:
        item_name: Product name (exact or alias).
    """
    resolved = _resolve_item_name(item_name) or item_name
    price = _get_unit_price(resolved)
    if price == 0:
        return f"Item '{item_name}' not found in catalog."
    return f"{resolved}: ${price:.2f} per unit"


# --- Tools for sales / fulfillment agent ---

@tool
def estimate_delivery_date(total_quantity: int, as_of_date: str, needs_restock: bool) -> str:
    """Estimate when an order can be delivered to the customer.

    Args:
        total_quantity: Total units in the order.
        as_of_date: Order date in YYYY-MM-DD format.
        needs_restock: Whether a supplier restock is required first.
    """
    if not needs_restock:
        earliest = as_of_date
    else:
        earliest = get_supplier_delivery_date(as_of_date, total_quantity)
    return f"Estimated customer delivery date: {earliest}"


@tool
def finalize_sale(items_json: str, total_amount: float, as_of_date: str) -> str:
    """Record sales transactions and deduct inventory for each line item.

    Args:
        items_json: JSON list of items with item_name and quantity fields.
        total_amount: Quoted total price charged to the customer.
        as_of_date: Sale date in YYYY-MM-DD format.
    """
    parsed = _parse_line_items(items_json)
    sold_lines = []
    errors = []

    for entry in parsed:
        if not entry["resolved"]:
            errors.append(f"Skipped unresolvable item: {entry['item_name']}")
            continue
        item_name = entry["item_name"]
        qty = entry["quantity"]
        stock_df = get_stock_level(item_name, as_of_date)
        current = int(stock_df["current_stock"].iloc[0])
        if current < qty:
            errors.append(
                f"Insufficient stock for {item_name}: need {qty}, have {current}"
            )
            continue
        unit_price = _get_unit_price(item_name)
        line_price = unit_price * qty
        create_transaction(item_name, "sales", qty, line_price, as_of_date)
        sold_lines.append(f"Sold {qty} x {item_name} (${line_price:.2f})")

    if not sold_lines:
        return "Sale NOT completed.\n" + "\n".join(errors)

    summary = "Sale completed:\n" + "\n".join(sold_lines)
    summary += f"\nLine-item revenue: ${sum(_get_unit_price(e['item_name']) * e['quantity'] for e in parsed if e['resolved']):.2f}"
    summary += f"\nQuoted total charged: ${total_amount:.2f}"
    if errors:
        summary += "\nWarnings:\n" + "\n".join(errors)
    return summary


@tool
def get_financial_status(as_of_date: str) -> str:
    """Return cash balance and inventory valuation as of a date.

    Args:
        as_of_date: Report date in YYYY-MM-DD format.
    """
    report = generate_financial_report(as_of_date)
    return (
        f"Financial status as of {as_of_date}:\n"
        f"  Cash: ${report['cash_balance']:.2f}\n"
        f"  Inventory value: ${report['inventory_value']:.2f}\n"
        f"  Total assets: ${report['total_assets']:.2f}"
    )


# --- Agent definitions (4 agents + orchestrator = 5 max) ---

class InventoryAgent(ToolCallingAgent):
    def __init__(self, llm_model):
        super().__init__(
            tools=[
                list_catalog_items,
                get_inventory_snapshot,
                check_items_availability,
                place_restock_order,
                auto_restock_if_needed,
            ],
            model=llm_model,
            name="inventory_agent",
            description=(
                "Manages warehouse inventory. Checks stock levels, identifies shortages, "
                "and places supplier restock orders when needed."
            ),
        )


class QuotingAgent(ToolCallingAgent):
    def __init__(self, llm_model):
        super().__init__(
            tools=[
                search_historical_quotes,
                calculate_quote,
                get_pricing_for_item,
                list_catalog_items,
            ],
            model=llm_model,
            name="quoting_agent",
            description=(
                "Generates competitive price quotes using catalog prices, bulk discounts, "
                "and historical quote data."
            ),
        )


class SalesAgent(ToolCallingAgent):
    def __init__(self, llm_model):
        super().__init__(
            tools=[
                finalize_sale,
                estimate_delivery_date,
                get_financial_status,
                check_items_availability,
            ],
            model=llm_model,
            name="sales_agent",
            description=(
                "Finalizes customer orders, records sales transactions, and confirms "
                "delivery timelines."
            ),
        )


def _parse_quote_total(quote_text: str) -> float:
    """Extract the quoted dollar total from agent output."""
    patterns = [
        r"QUOTE_TOTAL:\s*\$?\s*([\d,]+\.?\d*)",
        r"FINAL TOTAL:\s*\*?\*?\s*\$?\s*([\d,]+\.?\d*)",
        r"TOTAL:\s*\*?\*?\s*\$?\s*([\d,]+\.?\d*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, quote_text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            digits = re.findall(r"\d+\.?\d*", raw)
            if digits:
                try:
                    return float(digits[0])
                except ValueError:
                    continue
    return 0.0


def _agent_result_to_str(result) -> str:
    """Normalize smolagents run() output to a string for parsing."""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        if "PARSED_ITEMS_JSON" in result:
            items = result["PARSED_ITEMS_JSON"]
            return f"PARSED_ITEMS_JSON\n{json.dumps(items)}"
        return json.dumps(result)
    if isinstance(result, list):
        return json.dumps(result)
    return str(result)


def _extract_parsed_items(agent_result) -> str:
    """Extract a JSON items list from agent output (string or dict)."""
    if isinstance(agent_result, dict):
        if "PARSED_ITEMS_JSON" in agent_result:
            return json.dumps(agent_result["PARSED_ITEMS_JSON"])
        for value in agent_result.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                if "item_name" in value[0] and "quantity" in value[0]:
                    return json.dumps(value)

    text = _agent_result_to_str(agent_result)

    match = re.search(r"PARSED_ITEMS_JSON\s*[:=\s]*(\[.*?\])", text, re.DOTALL)
    if match:
        return match.group(1)

    match = re.search(r"(\[\s*\{[\s\S]*?\"item_name\"[\s\S]*?\}\s*\])", text)
    if match:
        return match.group(1)

    return "[]"


class OrchestratorAgent:
    """Coordinates inventory, quoting, and sales agents for each customer request."""

    def __init__(self, llm_model):
        self.inventory = InventoryAgent(llm_model)
        self.quoting = QuotingAgent(llm_model)
        self.sales = SalesAgent(llm_model)

    def handle_request(self, customer_request: str, request_date: str) -> str:
        deadline = _extract_deadline(customer_request)
        _set_request_context(request_date, deadline)

        inventory_prompt = f"""
Customer request (received {request_date}):
{customer_request}

Your tasks:
1. Parse the requested items and map them to exact catalog names.
2. Use check_items_availability with a JSON items list and as_of_date="{request_date}".
3. For any shortages, call auto_restock_if_needed with the same JSON and date.
4. Report stock status and any restock actions taken.

Return a JSON items list like [{{"item_name":"A4 paper","quantity":200}}] at the end
under the heading PARSED_ITEMS_JSON so downstream agents can use it.
"""
        inventory_result = self.inventory.run(inventory_prompt)
        inventory_text = _agent_result_to_str(inventory_result)

        parsed_json = _extract_parsed_items(inventory_result)

        quoting_prompt = f"""
Customer request (received {request_date}, deadline {deadline or 'not specified'}):
{customer_request}

Inventory agent report:
{inventory_text}

Parsed items JSON: {parsed_json}

Your tasks:
1. Search historical quotes for relevant keywords from this request.
2. Calculate a quote using calculate_quote with the parsed items JSON and as_of_date="{request_date}".
3. Apply bulk discounts. Provide a friendly explanation matching our historical pricing style.

End with QUOTE_TOTAL: $<amount>
"""
        quote_result = self.quoting.run(quoting_prompt)
        quote_text = _agent_result_to_str(quote_result)

        quote_total = _parse_quote_total(quote_text)

        needs_restock = any(
            s in inventory_text
            for s in ("LOW:", "Reorder", "Restock order placed", "Insufficient")
        )
        try:
            total_qty = sum(e.get("quantity", 0) for e in json.loads(parsed_json))
        except (json.JSONDecodeError, TypeError):
            total_qty = 0

        sales_prompt = f"""
Customer request (received {request_date}, deadline {deadline or 'not specified'}):
{customer_request}

Inventory report:
{inventory_text}

Quote:
{quote_text}
Quote total: ${quote_total:.2f}
Parsed items JSON: {parsed_json}

Your tasks:
1. Verify items are available (or will be after restock) using check_items_availability.
2. Estimate delivery with estimate_delivery_date (total_quantity={total_qty}, as_of_date="{request_date}", needs_restock={str(needs_restock).lower()}).
3. If stock is sufficient NOW, finalize the sale with finalize_sale using parsed JSON, total={quote_total}, date="{request_date}".
4. If deadline {deadline or 'unknown'} cannot be met, explain why instead of finalizing.
5. Report final financial status with get_financial_status.

Provide a complete customer-facing response with quote, delivery date, and order status.
"""
        sales_result = self.sales.run(sales_prompt)
        sales_text = _agent_result_to_str(sales_result)

        return (
            f"=== Beaver's Choice Paper Company Response ===\n\n"
            f"**Quote & Pricing:**\n{quote_text}\n\n"
            f"**Inventory & Fulfillment:**\n{inventory_text}\n\n"
            f"**Order Status:**\n{sales_text}"
        )


def create_orchestrator() -> OrchestratorAgent:
    return OrchestratorAgent(_get_model())


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############
    orchestrator = create_orchestrator()

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############
        response = orchestrator.handle_request(request_with_date, request_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
