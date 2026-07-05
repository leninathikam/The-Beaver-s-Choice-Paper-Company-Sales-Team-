"""Compatibility launcher for the Beaver's Choice Paper Company project."""

__all__ = ["main", "run_test_scenarios"]


def main() -> None:
    from beavers_choice.app import main as app_main

    app_main()


def run_test_scenarios():
    from beavers_choice.app import run_test_scenarios as app_run_test_scenarios

    return app_run_test_scenarios()


if __name__ == "__main__":
    main()