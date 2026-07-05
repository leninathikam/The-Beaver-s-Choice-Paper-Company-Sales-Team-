import json
import re
from datetime import datetime


def extract_deadline(text: str) -> str:
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


def parse_quote_total(quote_text: str) -> float:
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


def agent_result_to_str(result) -> str:
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


def extract_parsed_items(agent_result) -> str:
    if isinstance(agent_result, dict):
        if "PARSED_ITEMS_JSON" in agent_result:
            return json.dumps(agent_result["PARSED_ITEMS_JSON"])
        for value in agent_result.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                if "item_name" in value[0] and "quantity" in value[0]:
                    return json.dumps(value)

    text = agent_result_to_str(agent_result)
    match = re.search(r"PARSED_ITEMS_JSON\s*[:=\s]*(\[.*?\])", text, re.DOTALL)
    if match:
        return match.group(1)

    match = re.search(r"(\[\s*\{[\s\S]*?\"item_name\"[\s\S]*?\}\s*\])", text)
    if match:
        return match.group(1)

    return "[]"