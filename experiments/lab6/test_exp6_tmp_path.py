"""Experiment 6: every run gets a new isolated tmp_path."""

import json
from pathlib import Path

from employee_domain.adapters import JsonReportExporter

ROOT = Path(__file__).resolve().parents[2]


def test_report_is_written_only_to_tmp_path(tmp_path: Path) -> None:
    before = sorted(p.name for p in ROOT.iterdir())
    target = tmp_path / "report.json"
    target.write_text(JsonReportExporter().export([]), encoding="utf-8")
    print(f"\n  tmp_path = {tmp_path}")
    assert json.loads(target.read_text(encoding="utf-8")) == []
    assert list(tmp_path.iterdir()) == [target]           # empty before the test
    assert sorted(p.name for p in ROOT.iterdir()) == before  # repo untouched
