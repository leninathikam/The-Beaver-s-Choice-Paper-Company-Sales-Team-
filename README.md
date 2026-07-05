# Beaver's Choice Paper Company

Inventory, quoting, and sales orchestration for a paper supplier built with `smolagents` and SQLite.

## Layout

- `beavers_choice/` contains the actual application package
- `data/input/` is the canonical home for input CSVs
- `data/runtime/` stores the SQLite database created at runtime
- `outputs/` stores generated reports like `test_results.csv`
- `project_starter.py` is a compatibility launcher for the original entry point
- `workflow_diagram.png` and `design_notes.txt` document the submission context

## Run

1. Set `OPENAI_API_KEY` in `.env`
2. Run `python project_starter.py`

You can also run `python -m beavers_choice` from the repository root.
