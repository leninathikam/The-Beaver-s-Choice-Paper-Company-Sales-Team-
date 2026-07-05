import os

import pandas as pd
from smolagents import OpenAIServerModel, tool

from .catalog import bulk_discount_rate, get_unit_price, parse_line_items, paper_supplies, resolve_item_name
from .config import API_BASE, DB_ENGINE, ENV_VAR_NAME, MODEL_ID
from .database import (
    create_transaction,
    generate_financial_report,
    get_all_inventory,
    get_cash_balance,
    get_stock_level,
    get_supplier_delivery_date,
    search_quote_history,
)

model = None


def get_model() -> OpenAIServerModel:
    global model
    if model is not None:
        return model
    api_key = os.getenv(ENV_VAR_NAME)
    if not api_key:
        raise ValueError(
            f"{ENV_VAR_NAME} not found. Create a .env file in this folder:\n"
            f"  {ENV_VAR_NAME}=your_api_key_here\n"
            "Set your API key in the project .env file."
        )
    model = OpenAIServerModel(model_id=MODEL_ID, api_base=API_BASE, api_key=api_key)
    return model


@tool
def list_catalog_items() -> str:
    """Return all paper products the company sells with unit prices."""
    lines = [f"- {item['item_name']}: ${item['unit_price']:.2f} ({item['category']})" for item in paper_supplies]
    return "Available catalog items:\n" + "\n".join(lines)


@tool
def get_inventory_snapshot(as_of_date: str) -> str:
    """Return current stock levels for all in-stock items as of a given date."""
    stock = get_all_inventory(as_of_date)
    if not stock:
        return f"No inventory on hand as of {as_of_date}."
    lines = [f"- {name}: {qty} units" for name, qty in sorted(stock.items())]
    return f"Inventory as of {as_of_date}:\n" + "\n".join(lines)


@tool
def check_items_availability(items_json: str, as_of_date: str) -> str:
    """Check whether requested items are in stock."""
    parsed = parse_line_items(items_json)
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
            results.append(f"LOW: {entry['item_name']} — need {needed}, have {current}, short {shortfall}")
            reorder_needed.append({"item_name": entry["item_name"], "shortfall": shortfall, "needed": needed})
    summary = "\n".join(results)
    if reorder_needed:
        summary += "\n\nReorder recommended for: " + ", ".join(r["item_name"] for r in reorder_needed)
    return summary


@tool
def place_restock_order(item_name: str, quantity: int, as_of_date: str) -> str:
    """Place a supplier stock order when inventory is low."""
    resolved = resolve_item_name(item_name) or item_name
    unit_price = get_unit_price(resolved)
    if unit_price == 0:
        return f"Cannot reorder '{item_name}': item not found in catalog."

    order_qty = max(quantity, 100)
    total_cost = order_qty * unit_price
    cash = get_cash_balance(as_of_date)
    if cash < total_cost:
        return f"Insufficient cash to reorder {resolved}. Need ${total_cost:.2f}, have ${cash:.2f}."

    delivery = get_supplier_delivery_date(as_of_date, order_qty)
    create_transaction(resolved, "stock_orders", order_qty, total_cost, as_of_date)
    return f"Restock order placed: {order_qty} units of {resolved} (${total_cost:.2f}). Supplier delivery expected by {delivery}."


@tool
def auto_restock_if_needed(items_json: str, as_of_date: str) -> str:
    """Automatically reorder items below minimum stock or insufficient for the order."""
    parsed = parse_line_items(items_json)
    actions = []
    for entry in parsed:
        if not entry["resolved"]:
            continue
        item_name = entry["item_name"]
        stock_df = get_stock_level(item_name, as_of_date)
        current = int(stock_df["current_stock"].iloc[0])
        needed = entry["quantity"]

        min_level_df = pd.read_sql(
            "SELECT min_stock_level FROM inventory WHERE item_name = :name",
            DB_ENGINE,
            params={"name": item_name},
        )
        min_level = int(min_level_df.iloc[0]["min_stock_level"]) if not min_level_df.empty else 100

        if current >= needed and current >= min_level:
            actions.append(f"No restock needed for {item_name} (stock: {current}).")
            continue

        reorder_qty = max(needed - current, min_level * 2)
        result = place_restock_order(item_name, reorder_qty, as_of_date)
        actions.append(result)
    return "\n".join(actions) if actions else "All items sufficiently stocked."


@tool
def search_historical_quotes(search_terms: str) -> str:
    """Search past quotes by keywords to inform pricing strategy."""
    terms = [t.strip() for t in search_terms.split(",") if t.strip()]
    if not terms:
        terms = ["paper"]
    matches = search_quote_history(terms, limit=5)
    if not matches:
        return "No matching historical quotes found."
    lines = []
    for q in matches:
        lines.append(f"- ${q['total_amount']:.0f} | {q['job_type']}/{q['event_type']} | {q['quote_explanation'][:120]}...")
    return "Historical quotes:\n" + "\n".join(lines)


@tool
def calculate_quote(items_json: str, as_of_date: str) -> str:
    """Calculate a price quote with bulk discounts."""
    parsed = parse_line_items(items_json)
    lines = []
    subtotal = 0.0
    total_units = 0
    unavailable = []

    for entry in parsed:
        if not entry["resolved"]:
            unavailable.append(entry["item_name"])
            continue
        price = get_unit_price(entry["item_name"])
        line_total = price * entry["quantity"]
        subtotal += line_total
        total_units += entry["quantity"]
        lines.append(f"  {entry['item_name']}: {entry['quantity']} x ${price:.2f} = ${line_total:.2f}")

    discount_rate = bulk_discount_rate(total_units)
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
    """Look up the unit price for a specific catalog item."""
    resolved = resolve_item_name(item_name) or item_name
    price = get_unit_price(resolved)
    if price == 0:
        return f"Item '{item_name}' not found in catalog."
    return f"{resolved}: ${price:.2f} per unit"


@tool
def estimate_delivery_date(total_quantity: int, as_of_date: str, needs_restock: bool) -> str:
    """Estimate when an order can be delivered to the customer."""
    if not needs_restock:
        earliest = as_of_date
    else:
        earliest = get_supplier_delivery_date(as_of_date, total_quantity)
    return f"Estimated customer delivery date: {earliest}"


@tool
def finalize_sale(items_json: str, total_amount: float, as_of_date: str) -> str:
    """Record sales transactions and deduct inventory for each line item."""
    parsed = parse_line_items(items_json)
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
            errors.append(f"Insufficient stock for {item_name}: need {qty}, have {current}")
            continue
        unit_price = get_unit_price(item_name)
        line_price = unit_price * qty
        create_transaction(item_name, "sales", qty, line_price, as_of_date)
        sold_lines.append(f"Sold {qty} x {item_name} (${line_price:.2f})")

    if not sold_lines:
        return "Sale NOT completed.\n" + "\n".join(errors)

    summary = "Sale completed:\n" + "\n".join(sold_lines)
    summary += f"\nLine-item revenue: ${sum(get_unit_price(e['item_name']) * e['quantity'] for e in parsed if e['resolved']):.2f}"
    summary += f"\nQuoted total charged: ${total_amount:.2f}"
    if errors:
        summary += "\nWarnings:\n" + "\n".join(errors)
    return summary


@tool
def get_financial_status(as_of_date: str) -> str:
    """Return cash balance and inventory valuation as of a date."""
    report = generate_financial_report(as_of_date)
    return (
        f"Financial status as of {as_of_date}:\n"
        f"  Cash: ${report['cash_balance']:.2f}\n"
        f"  Inventory value: ${report['inventory_value']:.2f}\n"
        f"  Total assets: ${report['total_assets']:.2f}"
    )