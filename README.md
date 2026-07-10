# Beaver's Choice Paper Company

Inventory, quoting, and sales orchestration for a paper supplier built with `smolagents` and SQLite.

## Streamlit demo (recruiter showcase)

### Local

```bash
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
streamlit run streamlit_app.py
```

### Deploy free on Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy with **Main file path**: `streamlit_app.py`
4. In **Secrets**, add:

```toml
OPENAI_API_KEY = "sk-..."
# only if using Vocareum / custom gateway
# OPENAI_BASE_URL = "https://openai.vocareum.com/v1"
```

Also works on **Render** with:
`streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`

## Layout

- `streamlit_app.py` — interactive sales-desk demo
- `beavers_choice/` — application package (agents, tools, SQLite)
- `data/input/` — input CSVs
- `data/runtime/` — SQLite database created at runtime
- `outputs/` — generated reports
- `project_starter.py` — CLI compatibility launcher

## CLI run

1. Set `OPENAI_API_KEY` in `.env`
2. Run `python project_starter.py`

You can also run `python -m beavers_choice` from the repository root.
