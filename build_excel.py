"""Build TestCaseDocument_<Group>_v0.1.xlsx from the course template.

Reads:  template/TestCaseDocument__GroupNumber__v0.1.xlsx
        results/api_results.json   (run api-tests/run_tests.py first)
        ui-tests/ui_test_cases.py
        members.json
Writes: TestCaseDocument_<Group>_v0.1.xlsx
"""
import json, os, shutil, sys
from datetime import date
from copy import copy
import openpyxl
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ui-tests"))
from ui_test_cases import UI_CASES  # noqa: E402

cfg = json.load(open(os.path.join(HERE, "members.json"), encoding="utf-8"))
api = json.load(open(os.path.join(HERE, "results", "api_results.json"), encoding="utf-8"))
group = cfg["group_number"]
out = os.path.join(HERE, f"TestCaseDocument_{group}_v0.1.xlsx")
shutil.copy(os.path.join(HERE, "template", "TestCaseDocument__GroupNumber__v0.1.xlsx"), out)

wb = openpyxl.load_workbook(out)
ws = wb["Template"]
STATUS = {"Pass": "Passed", "Fail": "Failed", "Blocked": "Blocked"}


def tester(m):
    info = cfg["members"][m]
    return f"{m} - {info['id']}"


rows = []  # lists are test-case rows; ("SEP", m) marks the start of a member's section
for m in ("M1", "M2", "M3", "M4", "M5", "M6"):
    rows.append(("SEP", m))
    for r in (x for x in api["results"] if x["member"] == m):
        rows.append([
            r["id"], r["title"],
            f"{r['description']}\nEndpoint: {r['endpoint']}\nRole/Token: {r['role']}",
            r["precondition"], r["steps"], r["data"], r["expected"], r["actual"], "API",
            STATUS[r["status"]], tester(m), cfg["defects"].get(r["id"], ""),
        ])
    for (tid, title, url, role, pre, steps, data, exp) in UI_CASES[m]:
        rows.append([
            tid, title, f"{title}\nPage URL: {url}\nRole: {role}", pre, steps, data, exp, "",
            "UI", "Not Executed", tester(m), "",
        ])

# keep the template's style of the first data row, clear the sample rows
style_src = [ws.cell(row=3, column=c) for c in range(1, 13)]
styles = [(copy(c.font), copy(c.border), copy(c.fill)) for c in style_src]
ws.delete_rows(3, ws.max_row)
wrap = Alignment(wrap_text=True, vertical="top")
thick = Side(style="medium")
sep_rows = []
for i, row in enumerate(rows, start=3):
    if isinstance(row, tuple):  # member section header (bold, no colour: printed in B&W)
        m = row[1]; info = cfg["members"][m]
        ws.cell(row=i, column=1, value=f"{m}  |  {info['id']} - {info['name']}  |  {info['modules']}  "
                                       f"|  TC_API_{m}_01-15, TC_UI_{m}_01-15")
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=12)
        ws.cell(row=i, column=1).font = Font(bold=True, size=13)
        ws.cell(row=i, column=1).alignment = Alignment(vertical="center")
        for c in range(1, 13):
            ws.cell(row=i, column=c).border = Border(top=thick, bottom=thick,
                                                     left=thick if c == 1 else None,
                                                     right=thick if c == 12 else None)
        ws.row_dimensions[i].height = 26
        if i > 3:
            ws.row_breaks.append(Break(id=i - 1))  # each member starts on a new printed page
        sep_rows.append(i)
        continue
    for c, val in enumerate(row, start=1):
        cell = ws.cell(row=i, column=c, value=val)
        f, b, fl = styles[c - 1]
        cell.font, cell.border, cell.fill, cell.alignment = f, b, fl, wrap
last = 2 + len(rows)
for col, w in zip("ABCDEFGHIJKL", (15, 34, 40, 30, 42, 34, 42, 42, 8, 13, 16, 10)):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "B3"
ws.auto_filter.ref = f"A2:L{last}"
ws.data_validations.dataValidation = []
dv1 = DataValidation(type="list", formula1='"Passed,Failed,Blocked,Not Executed"', allow_blank=True)
dv2 = DataValidation(type="list", formula1='"UI,API"', allow_blank=True)
dv1.add(f"J3:J{last}"); dv2.add(f"I3:I{last}")
ws.add_data_validation(dv1); ws.add_data_validation(dv2)
for i in range(3, last + 1):  # bold Failed rows instead of colour (printed in black & white)
    if ws.cell(row=i, column=10).value == "Failed":
        ws.cell(row=i, column=10).font = Font(bold=True)


def print_setup(sheet, title_rows=None):
    """Lecturer: hard copy, A4/A3, black & white, one document per group."""
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A3
    sheet.page_setup.fitToWidth, sheet.page_setup.fitToHeight = 1, 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.print_options.gridLines = True
    sheet.page_setup.blackAndWhite = True
    if title_rows:
        sheet.print_title_rows = title_rows
    sheet.oddHeader.right.text = f"{group} - IS4600 Task 1"
    sheet.oddFooter.center.text = "Page &P of &N"


print_setup(ws, "2:2")

# ---- Summary sheet
s = wb["Summary"]
s["C3"] = "QA Training App - Admin App, Client App and Backend API (all modules)"
s["C4"] = "v0.1"
s["E4"] = "16/11/2026"
s["G4"] = date.today().strftime("%d/%m/%Y")
s["C5"] = "QA_Training_App_SRS_v2.1.pdf"
s["C6"] = "Swagger / OpenAPI (http://localhost:8080/swagger-ui.html)"
s["C8"] = "v0.1"
s["D8"] = f"{group} (all members)"
n_tc = sum(1 for r in rows if isinstance(r, list))
s["E8"] = (f"Initial test case design: {n_tc} test cases (15 API + 15 UI per member). "
           f"API cases executed on {api['executed_at'][:10]}; UI not executed (no UI in this release).")
s["C12"] = "All modules"
rng = f"Template!J3:J{last}", f"Template!I3:I{last}"
for r, kind in ((12, "D12"), (13, "D13")):
    for col in "FGHI":
        s[f"{col}{r}"] = f"=COUNTIFS({rng[0]},{col}11,{rng[1]},{kind})"

# ---- Module Division sheet (required by the instructions, section 4.3)
md = wb.create_sheet("Module Division", 1)
head = ["Member", "Student ID", "Name", "SRS modules", "API endpoints", "API TC IDs", "UI TC IDs"]
md.append(head)
for m, info in cfg["members"].items():
    md.append([m, info["id"], info["name"], info["modules"], cfg["api_endpoints"][m],
               f"TC_API_{m}_01 - TC_API_{m}_15", f"TC_UI_{m}_01 - TC_UI_{m}_15"])
md.append([])
md.append(["Rule", "Cross-cutting checks (401/403, wrong-app login, deactivated tokens) are written by each member only "
           "for the endpoints/pages they own, so no scenario is duplicated."])
md.append([])
md.append(["Per-member results", "API Passed", "API Failed", "API Blocked", "UI Not Executed", "Total"])
hdr = md.max_row
for m, info in cfg["members"].items():
    t = f'"{m} - {info["id"]}"'
    K, I, J = f"Template!K3:K{last}", f"Template!I3:I{last}", f"Template!J3:J{last}"
    md.append([f"{m} - {info['name']}",
               f'=COUNTIFS({K},{t},{I},"API",{J},"Passed")', f'=COUNTIFS({K},{t},{I},"API",{J},"Failed")',
               f'=COUNTIFS({K},{t},{I},"API",{J},"Blocked")', f'=COUNTIFS({K},{t},{I},"UI",{J},"Not Executed")',
               f"=COUNTIF({K},{t})"])
for c in list(md[1]) + list(md[hdr]):
    c.font = Font(bold=True)
for col, w in zip("ABCDEFG", (9, 16, 22, 55, 60, 26, 24)):
    md.column_dimensions[col].width = w
for row in md.iter_rows(min_row=2):
    for c in row:
        c.alignment = wrap
print_setup(md)
print_setup(s)

wb.save(out)
print(f"Wrote {out}  ({n_tc} test cases, {len(sep_rows)} member sections)")
