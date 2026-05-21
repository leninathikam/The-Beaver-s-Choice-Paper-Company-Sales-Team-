"""Generate rubric-compliant workflow_diagram.png with tools and helper functions."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(18, 14))
ax.set_xlim(0, 18)
ax.set_ylim(0, 14)
ax.axis("off")
ax.set_title(
    "Beaver's Choice Paper — Multi-Agent System Architecture",
    fontsize=17, fontweight="bold", pad=18,
)

def box(x, y, w, h, text, color, fs=7.5):
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
                          facecolor=color, edgecolor="#333", linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)

def arrow(x1, y1, x2, y2, style="-|>"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color="#444", lw=1.2))

# ── Customer ──
box(7, 13, 4, 0.7, "Customer Text Request\n(items · quantities · deadline · date)", "#E8F4FD", 8)
arrow(9, 13, 9, 12.35)

# ── Orchestrator ──
box(5.5, 11.4, 7, 0.95,
    "ORCHESTRATOR AGENT\nReceives inquiry · extracts dates · delegates to workers · assembles response",
    "#FFD966", 8)
arrow(9, 11.4, 3.5, 10.55)
arrow(9, 11.4, 9, 10.55)
arrow(9, 11.4, 14.5, 10.55)

# ── Worker Agents ──
box(0.3, 9.3, 5.4, 1.25,
    "INVENTORY AGENT\nResponsibility: stock queries & supplier reorder decisions\n(no overlap with quoting/sales)",
    "#B6D7A8", 7.5)
box(6.3, 9.3, 5.4, 1.25,
    "QUOTING AGENT\nResponsibility: price calculation & bulk discount strategy\n(no overlap with inventory/sales)",
    "#F9CB9C", 7.5)
box(12.3, 9.3, 5.4, 1.25,
    "SALES AGENT\nResponsibility: order fulfillment & delivery confirmation\n(no overlap with inventory/quoting)",
    "#D5A6BD", 7.5)

# ── Tools per agent (with helper functions) ──
inv_tools = (
    "TOOLS → HELPER FUNCTIONS\n"
    "─────────────────────────\n"
    "get_inventory_snapshot → get_all_inventory\n"
    "check_items_availability → get_stock_level\n"
    "place_restock_order → create_transaction,\n"
    "  get_cash_balance, get_supplier_delivery_date\n"
    "auto_restock_if_needed → get_stock_level,\n"
    "  place_restock_order (above helpers)\n"
    "list_catalog_items → paper_supplies catalog"
)
quote_tools = (
    "TOOLS → HELPER FUNCTIONS\n"
    "─────────────────────────\n"
    "search_historical_quotes → search_quote_history\n"
    "calculate_quote → paper_supplies prices\n"
    "get_pricing_for_item → paper_supplies prices\n"
    "list_catalog_items → paper_supplies catalog"
)
sales_tools = (
    "TOOLS → HELPER FUNCTIONS\n"
    "─────────────────────────\n"
    "finalize_sale → create_transaction,\n"
    "  get_stock_level\n"
    "estimate_delivery_date →\n"
    "  get_supplier_delivery_date\n"
    "get_financial_status →\n"
    "  generate_financial_report\n"
    "check_items_availability → get_stock_level"
)

box(0.3, 6.5, 5.4, 2.6, inv_tools, "#E2EFDA", 7)
box(6.3, 6.5, 5.4, 2.6, quote_tools, "#FCE5CD", 7)
box(12.3, 6.5, 5.4, 2.6, sales_tools, "#EAD1DC", 7)

arrow(3, 9.3, 3, 9.1)
arrow(9, 9.3, 9, 9.1)
arrow(15, 9.3, 15, 9.1)

# ── Database ──
box(4, 3.8, 10, 1.1,
    "SQLite DATABASE (munder_difflin.db)\n"
    "Tables: inventory · transactions · quotes · quote_requests",
    "#D9D9D9", 8)

arrow(3, 6.5, 6, 4.9)
arrow(9, 6.5, 9, 4.9)
arrow(15, 6.5, 12, 4.9)

# Data flow labels
ax.text(4.5, 5.8, "read/write\nstock & orders", fontsize=6.5, color="#555", ha="center")
ax.text(9, 5.8, "read quote\nhistory", fontsize=6.5, color="#555", ha="center")
ax.text(13.5, 5.8, "write sales\nread stock", fontsize=6.5, color="#555", ha="center")

# ── Orchestration return path ──
arrow(3, 6.5, 5.5, 11.85, style="->")
arrow(9, 6.5, 9, 11.85, style="->")
arrow(15, 6.5, 12.5, 11.85, style="->")
ax.text(9, 11.1, "agent reports flow back to orchestrator", fontsize=7, color="#666", ha="center")

# ── Customer output ──
box(5.5, 1.8, 7, 1.0,
    "CUSTOMER RESPONSE (text)\n"
    "Quote breakdown · bulk discount rationale · delivery date · order status",
    "#E8F4FD", 8)
arrow(9, 3.8, 9, 2.8)

# Footer
ax.text(0.3, 0.5,
    "Framework: smolagents · Model: gpt-4o-mini · API: Vocareum proxy · Agents: 4 (+ orchestrator = 5 max)",
    fontsize=7.5, color="#666")

plt.tight_layout()
plt.savefig("workflow_diagram.png", dpi=160, bbox_inches="tight", facecolor="white")
print("Saved workflow_diagram.png")
