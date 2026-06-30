"""
CLI: Generate 2500+ synthetic Swedish farmers for ML training.

Usage:
    python -m backend.generate_farmers [--count 2500]
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import init_db, SessionLocal, engine, Base
from backend.app.services.synthetic_generator import seed_bulk_farmers


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Swedish farmers")
    parser.add_argument("--count", type=int, default=2500, help="Number of farmers to generate")
    args = parser.parse_args()

    print(f"Initializing database...")
    init_db()

    print(f"Generating {args.count} synthetic Swedish farmers...")
    print("This may take 2-3 minutes...")

    db = SessionLocal()
    try:
        total = seed_bulk_farmers(db, n_farmers=args.count)
        print(f"\nDone! Generated {total} total rows across all tables.")
        print(f"  Farmers: {args.count}")
        print(f"  Financial Records: {args.count * 3}")
        print(f"  Loans: ~{args.count * 2.5:.0f}")
        print(f"  Operational Data: {args.count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
