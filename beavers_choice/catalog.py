import json
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

paper_supplies = [
    {"item_name": "A4 paper", "category": "paper", "unit_price": 0.05},
    {"item_name": "Letter-sized paper", "category": "paper", "unit_price": 0.06},
    {"item_name": "Cardstock", "category": "paper", "unit_price": 0.15},
    {"item_name": "Colored paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Glossy paper", "category": "paper", "unit_price": 0.20},
    {"item_name": "Matte paper", "category": "paper", "unit_price": 0.18},
    {"item_name": "Recycled paper", "category": "paper", "unit_price": 0.08},
    {"item_name": "Eco-friendly paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Poster paper", "category": "paper", "unit_price": 0.25},
    {"item_name": "Banner paper", "category": "paper", "unit_price": 0.30},
    {"item_name": "Kraft paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Construction paper", "category": "paper", "unit_price": 0.07},
    {"item_name": "Wrapping paper", "category": "paper", "unit_price": 0.15},
    {"item_name": "Glitter paper", "category": "paper", "unit_price": 0.22},
    {"item_name": "Decorative paper", "category": "paper", "unit_price": 0.18},
    {"item_name": "Letterhead paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Legal-size paper", "category": "paper", "unit_price": 0.08},
    {"item_name": "Crepe paper", "category": "paper", "unit_price": 0.05},
    {"item_name": "Photo paper", "category": "paper", "unit_price": 0.25},
    {"item_name": "Uncoated paper", "category": "paper", "unit_price": 0.06},
    {"item_name": "Butcher paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Heavyweight paper", "category": "paper", "unit_price": 0.20},
    {"item_name": "Standard copy paper", "category": "paper", "unit_price": 0.04},
    {"item_name": "Bright-colored paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Patterned paper", "category": "paper", "unit_price": 0.15},
    {"item_name": "Paper plates", "category": "product", "unit_price": 0.10},
    {"item_name": "Paper cups", "category": "product", "unit_price": 0.08},
    {"item_name": "Paper napkins", "category": "product", "unit_price": 0.02},
    {"item_name": "Disposable cups", "category": "product", "unit_price": 0.10},
    {"item_name": "Table covers", "category": "product", "unit_price": 1.50},
    {"item_name": "Envelopes", "category": "product", "unit_price": 0.05},
    {"item_name": "Sticky notes", "category": "product", "unit_price": 0.03},
    {"item_name": "Notepads", "category": "product", "unit_price": 2.00},
    {"item_name": "Invitation cards", "category": "product", "unit_price": 0.50},
    {"item_name": "Flyers", "category": "product", "unit_price": 0.15},
    {"item_name": "Party streamers", "category": "product", "unit_price": 0.05},
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},
    {"item_name": "Paper party bags", "category": "product", "unit_price": 0.25},
    {"item_name": "Name tags with lanyards", "category": "product", "unit_price": 0.75},
    {"item_name": "Presentation folders", "category": "product", "unit_price": 0.50},
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},
    {"item_name": "100 lb cover stock", "category": "specialty", "unit_price": 0.50},
    {"item_name": "80 lb text paper", "category": "specialty", "unit_price": 0.40},
    {"item_name": "250 gsm cardstock", "category": "specialty", "unit_price": 0.30},
    {"item_name": "220 gsm poster paper", "category": "specialty", "unit_price": 0.35},
]


def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    np.random.seed(seed)
    num_items = int(len(paper_supplies) * coverage)
    selected_indices = np.random.choice(range(len(paper_supplies)), size=num_items, replace=False)
    selected_items = [paper_supplies[i] for i in selected_indices]
    inventory = []
    for item in selected_items:
        inventory.append(
            {
                "item_name": item["item_name"],
                "category": item["category"],
                "unit_price": item["unit_price"],
                "current_stock": np.random.randint(200, 800),
                "min_stock_level": np.random.randint(50, 150),
            }
        )
    return pd.DataFrame(inventory)


def resolve_item_name(name: str) -> Optional[str]:
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


def parse_line_items(items_json: str) -> List[Dict]:
    items = json.loads(items_json)
    parsed = []
    for entry in items:
        raw_name = entry.get("item_name") or entry.get("name", "")
        qty = int(entry.get("quantity") or entry.get("units", 0))
        resolved = resolve_item_name(raw_name)
        if not resolved:
            parsed.append({"item_name": raw_name, "quantity": qty, "resolved": False})
        else:
            parsed.append({"item_name": resolved, "quantity": qty, "resolved": True})
    return parsed


def bulk_discount_rate(total_units: int) -> float:
    if total_units >= 5000:
        return 0.15
    if total_units >= 1000:
        return 0.10
    if total_units >= 500:
        return 0.08
    if total_units >= 200:
        return 0.05
    return 0.0


def get_unit_price(item_name: str) -> float:
    for item in paper_supplies:
        if item["item_name"] == item_name:
            return item["unit_price"]
    return 0.0