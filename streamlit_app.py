"""Beaver's Choice Paper Company — recruiter-ready Streamlit demo."""

from __future__ import annotations

import os
from datetime import date

import streamlit as st

from beavers_choice.agents import create_orchestrator
from beavers_choice.catalog import paper_supplies
from beavers_choice.database import generate_financial_report, get_all_inventory, init_database

st.set_page_config(
    page_title="Beaver's Choice | AI Sales Team",
    page_icon="🦫",
    layout="wide",
)

SAMPLE_REQUESTS = [
    "I need 500 sheets of A4 paper and 200 envelopes for a conference next Friday.",
    "Please quote 1000 business cards and 50 poster boards for a product launch.",
    "We need 300 notebooks and 100 packs of sticky notes delivered by next week.",
]


def ensure_api_key() -> str | None:
    # Prefer Streamlit Cloud secrets; fall back to env / optional .env
    key = None
    try:
        key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("UDACITY_OPENAI_API_KEY")
    except Exception:
        pass

    if not key:
        try:
            from dotenv import load_dotenv
            from beavers_choice.config import REPO_ROOT

            load_dotenv(REPO_ROOT / ".env")
            load_dotenv()
        except ImportError:
            pass
        key = os.getenv("OPENAI_API_KEY") or os.getenv("UDACITY_OPENAI_API_KEY")

    if key and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = key
    return key


@st.cache_resource(show_spinner="Initializing inventory database...")
def bootstrap_db():
    return init_database()


def main():
    st.title("Beaver's Choice Paper Company")
    st.caption(
        "Multi-agent sales desk — inventory, quoting, and order finalization with smolagents + SQLite"
    )

    api_key = ensure_api_key()
    bootstrap_db()

    with st.sidebar:
        st.header("About")
        st.write(
            "Three specialist agents (Inventory, Quoting, Sales) are coordinated by an "
            "orchestrator to handle customer quote requests against a live SQLite inventory."
        )
        st.markdown(
            "[GitHub repo](https://github.com/leninathikam/The-Beaver-s-Choice-Paper-Company-Sales-Team-)"
        )
        st.divider()
        st.write("OpenAI key:", "ready" if api_key else "missing")
        request_date = st.date_input("Request date", value=date(2025, 1, 15))
        if st.button("Reset database"):
            st.cache_resource.clear()
            bootstrap_db()
            st.success("Database re-seeded.")
            st.rerun()

        st.divider()
        st.subheader("Sample requests")
        for sample in SAMPLE_REQUESTS:
            if st.button(sample, use_container_width=True):
                st.session_state.pending_request = sample

    as_of = request_date.isoformat()
    report = generate_financial_report(as_of)
    inventory = get_all_inventory(as_of)

    m1, m2, m3 = st.columns(3)
    m1.metric("Cash balance", f"${report['cash_balance']:,.2f}")
    m2.metric("Inventory value", f"${report['inventory_value']:,.2f}")
    m3.metric("Total assets", f"${report['total_assets']:,.2f}")

    col_req, col_inv = st.columns([1.4, 1], gap="large")

    with col_inv:
        st.subheader("Catalog & stock")
        for item in paper_supplies:
            name = item["item_name"]
            stock = inventory.get(name, 0)
            st.markdown(
                f"**{name}** — ${item['unit_price']:.2f} · {item['category']}\n\n"
                f"On hand ({as_of}): **{stock}** units"
            )
            st.divider()

    with col_req:
        st.subheader("Customer request")
        default = st.session_state.pop("pending_request", "")
        request_text = st.text_area(
            "Describe what the customer needs",
            value=default,
            height=160,
            placeholder="e.g. I need 200 A4 paper reams and 50 poster boards by Jan 20.",
        )
        submit = st.button("Process with AI sales team", type="primary", use_container_width=True)

        if submit:
            if not api_key:
                st.error("Add OPENAI_API_KEY in Streamlit secrets or a local .env file.")
                return
            if not request_text.strip():
                st.warning("Enter a customer request first.")
                return

            with st.spinner("Inventory → Quoting → Sales agents working..."):
                try:
                    orchestrator = create_orchestrator()
                    response = orchestrator.handle_request(request_text.strip(), as_of)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Sales team failed: {exc}")
                    return

            st.subheader("Agent response")
            st.markdown(response)

            updated = generate_financial_report(as_of)
            st.subheader("Updated financials")
            c1, c2, c3 = st.columns(3)
            c1.metric("Cash", f"${updated['cash_balance']:,.2f}")
            c2.metric("Inventory", f"${updated['inventory_value']:,.2f}")
            c3.metric("Assets", f"${updated['total_assets']:,.2f}")


if __name__ == "__main__":
    main()
