import io
from datetime import datetime

import pandas as pd
from openpyxl import load_workbook

from canesense import reports, service

SC = dict(scenario="Simulate Dry Spell", records=28)


def frame():
    return service.scenario_frame("Simulate Dry Spell")


def test_pdf_generates_valid_document():
    pdf = reports.to_pdf(frame(), SC, datetime(2026, 3, 14, 9, 0))
    assert pdf[:5] == b"%PDF-" and len(pdf) > 10_000


def test_pdf_scope_changes_output_and_handles_one_row():
    d = frame()
    full = reports.to_pdf(d, SC, datetime(2026, 3, 14))
    one = reports.to_pdf(d.head(1), dict(SC, records=1), datetime(2026, 3, 14))
    assert one[:5] == b"%PDF-" and len(one) != len(full)


def test_pdf_academic_block_is_optional():
    d = frame()
    plain = reports.to_pdf(d, SC, datetime(2026, 3, 14))
    acad = reports.to_pdf(d, SC, datetime(2026, 3, 14), academic=dict(project="P", name="N", roll="R", batch="B", professor="Prof"))
    assert plain != acad


def test_csv_reflects_selected_records():
    d = frame()
    sel = d[d.urgency == "High"]
    csv = reports.to_csv(sel, dict(SC, records=len(sel)), datetime(2026, 3, 14)).decode()
    body = pd.read_csv(io.StringIO(csv), comment="#")
    assert len(body) == len(sel) and set(body["Urgency"]) == {"High"}
    assert "SYNTHETIC" in csv


def test_excel_has_expected_sheets_and_rows():
    d = frame()
    wb = load_workbook(io.BytesIO(reports.to_excel(d, SC, datetime(2026, 3, 14))))
    assert wb.sheetnames == ["Summary", "Plots", "Actions"]
    assert wb["Plots"].max_row == len(d) + 1
