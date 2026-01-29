import json
from collections import Counter
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "app.log"
SHEETS_PATH = Path(__file__).resolve().parents[1] / "logs" / "google_sheets.csv"


def main():
    print(f"[Visualizer] Reading logs from {LOG_PATH}")
    if not LOG_PATH.exists():
        print("[Visualizer] No log file found.")
        return

    categories = Counter()
    cb_states = Counter()
    services = Counter()

    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            categories[rec.get("category", "unknown")] += 1
            cb_states[rec.get("circuit_breaker_state", "")] += 1
            services[rec.get("service", "")] += 1

    print("\n[Summary]")
    print("- Events by category:")
    for k, v in categories.items():
        print(f"  {k}: {v}")

    print("- Circuit breaker states observed:")
    for k, v in cb_states.items():
        if k:
            print(f"  {k}: {v}")

    print("- Events by service:")
    for k, v in services.items():
        if k:
            print(f"  {k}: {v}")

    if SHEETS_PATH.exists():
        print(f"\n[Sheets Mock] CSV at {SHEETS_PATH} (first few lines):")
        try:
            with SHEETS_PATH.open("r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    print("  ", line.strip())
                    if i >= 5:
                        break
        except Exception:
            pass


if __name__ == "__main__":
    main()
