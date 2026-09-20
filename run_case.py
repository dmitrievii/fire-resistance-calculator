import argparse
from pathlib import Path

from standard_core.runner import run_case


def _main() -> None:
    parser = argparse.ArgumentParser(description="Run a supported СП 16.13330.2017 Phase 0.24 JSON case.")
    parser.add_argument("case", help="Path to a JSON case file")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    result = run_case(args.case, root)
    print(f"Case {result['case_id']} completed.")
    print(f"Action: {result['action']}")
    print("Reports written to reports/ and calculation output written to outputs/.")


if __name__ == "__main__":
    _main()
