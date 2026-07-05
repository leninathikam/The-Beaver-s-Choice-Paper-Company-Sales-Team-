import json

from smolagents import ToolCallingAgent

from .config import set_request_context
from .parsing import agent_result_to_str, extract_deadline, extract_parsed_items, parse_quote_total
from .tools import (
    auto_restock_if_needed,
    calculate_quote,
    check_items_availability,
    estimate_delivery_date,
    finalize_sale,
    get_financial_status,
    get_inventory_snapshot,
    get_model,
    get_pricing_for_item,
    list_catalog_items,
    place_restock_order,
    search_historical_quotes,
)


class InventoryAgent(ToolCallingAgent):
    def __init__(self, llm_model):
        super().__init__(
            tools=[list_catalog_items, get_inventory_snapshot, check_items_availability, place_restock_order, auto_restock_if_needed],
            model=llm_model,
            name="inventory_agent",
            description=(
                "Manages warehouse inventory. Checks stock levels, identifies shortages, and places supplier restock orders when needed."
            ),
        )


class QuotingAgent(ToolCallingAgent):
    def __init__(self, llm_model):
        super().__init__(
            tools=[search_historical_quotes, calculate_quote, get_pricing_for_item, list_catalog_items],
            model=llm_model,
            name="quoting_agent",
            description=("Generates competitive price quotes using catalog prices, bulk discounts, and historical quote data."),
        )


class SalesAgent(ToolCallingAgent):
    def __init__(self, llm_model):
        super().__init__(
            tools=[finalize_sale, estimate_delivery_date, get_financial_status, check_items_availability],
            model=llm_model,
            name="sales_agent",
            description=("Finalizes customer orders, records sales transactions, and confirms delivery timelines."),
        )


class OrchestratorAgent:
    """Coordinates inventory, quoting, and sales agents for each customer request."""

    def __init__(self, llm_model):
        self.inventory = InventoryAgent(llm_model)
        self.quoting = QuotingAgent(llm_model)
        self.sales = SalesAgent(llm_model)

    def handle_request(self, customer_request: str, request_date: str) -> str:
        deadline = extract_deadline(customer_request)
        set_request_context(request_date, deadline)

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
        inventory_text = agent_result_to_str(inventory_result)

        parsed_json = extract_parsed_items(inventory_result)

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
        quote_text = agent_result_to_str(quote_result)
        quote_total = parse_quote_total(quote_text)

        needs_restock = any(s in inventory_text for s in ("LOW:", "Reorder", "Restock order placed", "Insufficient"))
        try:
            total_qty = sum(e.get("quantity", 0) for e in json.loads(parsed_json))
        except (ValueError, TypeError, json.JSONDecodeError):
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
        sales_text = agent_result_to_str(sales_result)

        return (
            f"=== Beaver's Choice Paper Company Response ===\n\n"
            f"**Quote & Pricing:**\n{quote_text}\n\n"
            f"**Inventory & Fulfillment:**\n{inventory_text}\n\n"
            f"**Order Status:**\n{sales_text}"
        )


def create_orchestrator() -> OrchestratorAgent:
    return OrchestratorAgent(get_model())