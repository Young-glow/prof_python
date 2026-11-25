from collections import Counter

from data_processor.analytics import (
    average,
    average_salary_by_department,
    build_summary,
    calculate_average_salary,
    calculate_payroll,
    create_record,
    find_highest_paid,
    pipeline,
    salary_range,
    sort_items,
)
from data_processor.data import Employee, employees, generate_employees
from data_processor.decorators import operation_history, timings
from data_processor.processors import (
    count_by_department,
    create_department_filter,
    create_employee_index,
    create_salary_filter,
    filter_items,
    find_by_name,
    find_linear,
    get_unique_departments,
    group_by,
    group_nested,
)


def test_unique_departments() -> None:
    assert get_unique_departments(employees) == {"IT", "Finance", "HR", "Sales"}


def test_index_and_linear_search_agree() -> None:
    index = create_employee_index(employees)
    assert index[3] is find_linear(employees, 3)
    assert index.get(99) is None and find_linear(employees, 99) is None


def test_find_by_name() -> None:
    assert [e["id"] for e in find_by_name(employees, "kov")] == [1]


def test_salary_filter_closure() -> None:
    rich = create_salary_filter(50000)
    assert {e["id"] for e in filter_items(employees, rich)} == {1, 3, 8}
    middle = create_salary_filter(30000, 40000)
    assert {e["id"] for e in filter_items(employees, middle)} == {2, 6, 10}


def test_department_filter_args() -> None:
    hr_sales = create_department_filter("HR", "Sales")
    assert len(filter_items(employees, hr_sales)) == 4


def test_grouping_and_counter() -> None:
    groups = group_by(employees, "department")
    assert len(groups["IT"]) == 5
    assert count_by_department(employees) == Counter(
        {"IT": 5, "Finance": 3, "HR": 2, "Sales": 2}
    )
    nested = group_nested(employees, "department", "position")
    assert len(nested["IT"]["Python Developer"]) == 2


def test_aggregation() -> None:
    assert calculate_payroll(employees) == 503000
    assert round(calculate_average_salary(employees), 2) == 41916.67
    assert calculate_average_salary([]) == 0.0
    assert average_salary_by_department(employees)["Finance"] == 39666.666666666664
    best = find_highest_paid(employees)
    assert best is not None and best["name"] == "Iryna Bondar"
    assert find_highest_paid([]) is None
    assert salary_range(employees) == (26000.0, 68000.0)


def test_sorting() -> None:
    ranking = sort_items(employees, "salary", reverse=True)
    assert [e["id"] for e in ranking[:2]] == [3, 8]
    by_dept = sort_items(employees, "department", "name")
    assert by_dept[0]["department"] == "Finance"


def test_args_kwargs() -> None:
    assert average(10, 20, 30) == 20
    assert average() == 0.0
    record: Employee = create_record(id=13, name="Test", salary=1.0)
    assert record == {"id": 13, "name": "Test", "salary": 1.0}


def test_pipeline_and_summary() -> None:
    result = pipeline(
        employees,
        lambda items: filter_items(items, create_department_filter("IT")),
        lambda items: sort_items(items, "salary"),
    )
    assert [e["id"] for e in result] == [6, 12, 1, 8, 3]
    summary = build_summary(employees)
    assert summary["employees"] == 12 and summary["highest_paid"] == "Iryna Bondar"


def test_decorators() -> None:
    calculate_average_salary(employees)
    assert "calculate_average_salary" in timings
    get_unique_departments(employees)
    assert operation_history[-1] == "set comprehension: get_unique_departments"
    assert len(operation_history) <= 5


def test_generate_employees() -> None:
    data = generate_employees(100)
    assert len(data) == 100 and len(create_employee_index(data)) == 100
