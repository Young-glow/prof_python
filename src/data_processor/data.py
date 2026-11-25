"""Input data: a list of employee records and helpers to generate more."""

import random

Employee = dict[str, int | str | float]

# tuple: a fixed, immutable description of a record
FIELDS: tuple[str, ...] = ("id", "name", "position", "department", "salary")

# tuple: valid salary range (minimum, maximum), UAH
SALARY_RANGE: tuple[float, float] = (8000.0, 200000.0)

# list: ordered, mutable collection of records
employees: list[Employee] = [
    {"id": 1, "name": "Anna Koval", "position": "Python Developer",
     "department": "IT", "salary": 52000.0},
    {"id": 2, "name": "Oleh Melnyk", "position": "Accountant",
     "department": "Finance", "salary": 31000.0},
    {"id": 3, "name": "Iryna Bondar", "position": "Team Lead",
     "department": "IT", "salary": 68000.0},
    {"id": 4, "name": "Andrii Shevchenko", "position": "HR Manager",
     "department": "HR", "salary": 29000.0},
    {"id": 5, "name": "Maria Tkachenko", "position": "Financial Analyst",
     "department": "Finance", "salary": 41000.0},
    {"id": 6, "name": "Taras Lysenko", "position": "QA Engineer",
     "department": "IT", "salary": 38000.0},
    {"id": 7, "name": "Olena Kravets", "position": "Recruiter",
     "department": "HR", "salary": 26000.0},
    {"id": 8, "name": "Dmytro Savchenko", "position": "DevOps Engineer",
     "department": "IT", "salary": 61000.0},
    {"id": 9, "name": "Kateryna Moroz", "position": "Chief Accountant",
     "department": "Finance", "salary": 47000.0},
    {"id": 10, "name": "Petro Ivanenko", "position": "Sales Manager",
     "department": "Sales", "salary": 34000.0},
    {"id": 11, "name": "Sofiia Hnatiuk", "position": "Sales Representative",
     "department": "Sales", "salary": 27000.0},
    {"id": 12, "name": "Yurii Pavlenko", "position": "Python Developer",
     "department": "IT", "salary": 49000.0},
]

_DEPARTMENTS: tuple[str, ...] = ("IT", "Finance", "HR", "Sales", "Marketing")
_POSITIONS: tuple[str, ...] = ("Engineer", "Manager", "Analyst", "Specialist")


def generate_employees(count: int, seed: int = 2026) -> list[Employee]:
    """Generate `count` random employee records (used for the benchmark)."""
    generator = random.Random(seed)
    low, high = SALARY_RANGE
    return [
        {
            "id": number,
            "name": f"Employee {number}",
            "position": generator.choice(_POSITIONS),
            "department": generator.choice(_DEPARTMENTS),
            "salary": round(generator.uniform(low, high / 4), 2),
        }
        for number in range(1, count + 1)
    ]
