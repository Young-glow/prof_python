"""Demo data as external payloads (TypedDict)."""

from employee_domain.dto import EmployeePayload

DEPARTMENTS: dict[int, str] = {1: "IT", 2: "Finance", 3: "HR"}

PAYLOADS: list[EmployeePayload] = [
    {"id": 1, "name": "Anna Koval", "email": "anna.koval@company.ua",
     "salary": 52000, "role": "developer", "department": "IT",
     "level": "middle", "skills": ["Python", "Django"]},
    {"id": 3, "name": "Iryna Bondar", "email": "iryna.bondar@company.ua",
     "salary": 68000, "role": "manager", "department": "IT",
     "bonus_percent": 15},
    {"id": 6, "name": "Taras Lysenko", "email": "taras.lysenko@company.ua",
     "salary": 38000, "role": "developer", "department": "IT",
     "level": "junior", "skills": ["pytest", "Selenium"]},
    {"id": 8, "name": "Dmytro Savchenko", "email": "dmytro.savchenko@company.ua",
     "salary": 61000, "role": "developer", "department": "IT",
     "level": "senior", "skills": ["Docker", "Kubernetes", "Python"]},
    {"id": 9, "name": "Kateryna Moroz", "email": "kateryna.moroz@company.ua",
     "salary": 47000, "role": "manager", "department": "Finance",
     "bonus_percent": 12},
    {"id": 5, "name": "Maria Tkachenko", "email": "maria.tkachenko@company.ua",
     "salary": 41000, "role": "developer", "department": "Finance",
     "level": "middle", "skills": ["SQL", "Power BI"]},
    {"id": 4, "name": "Andrii Shevchenko", "email": "andrii.shevchenko@company.ua",
     "salary": 29000, "role": "manager", "department": "HR",
     "bonus_percent": 8},
    {"id": 12, "name": "Yurii Pavlenko", "email": "yurii.pavlenko@company.ua",
     "salary": 49000, "role": "developer", "department": "IT",
     "level": "middle", "skills": ["Python", "FastAPI"]},
]
