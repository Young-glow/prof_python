"""Generation of large test datasets."""

import csv
import random
from pathlib import Path

from stream_processor.models import CSV_HEADER

DEPARTMENTS = ("IT", "Finance", "HR", "Sales", "Marketing")
POSITIONS = ("Engineer", "Manager", "Analyst", "Specialist", "Accountant")
DATA_DIR = Path("data/generated")


def generate_file(path: Path, count: int, seed: int = 2026) -> Path:
    """Write `count` employee records; about 1% of them are invalid."""
    generator = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)
        for number in range(1, count + 1):
            salary: object = round(generator.uniform(15000, 120000), 2)
            if generator.random() < 0.01:
                salary = generator.choice(("error", "-100", ""))
            writer.writerow([
                number,
                f"employee {number}",
                generator.choice(POSITIONS),
                generator.choice(DEPARTMENTS),
                salary,
            ])
    return path


def dataset(count: int) -> Path:
    """Return a dataset with `count` records, creating it if needed."""
    path = DATA_DIR / f"employees_{count}.csv"
    if not path.exists():
        generate_file(path, count)
    return path
