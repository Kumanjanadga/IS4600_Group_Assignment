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
# Feature table: one block (UI row + API row) per member, in the template's own style.
CACHED = {}  # (sheet, cell) -> computed value, written next to each formula so viewers show numbers
tc_rows = [r for r in rows if isinstance(r, list)]
def count(member=None, kind=None, status=None):
    return sum(1 for r in tc_rows if (member is None or r[10] == member) and (kind is None or r[8] == kind)
               and (status is None or r[9] == status))
st = {r: [(copy(s.cell(r, c).font), copy(s.cell(r, c).border), copy(s.cell(r, c).fill),
           copy(s.cell(r, c).alignment), s.cell(r, c).number_format) for c in range(2, 10)] for r in (12, 13, 14)}
for rng_ in list(s.merged_cells.ranges):
    if rng_.min_row >= 12:
        s.unmerge_cells(str(rng_))
for r in range(12, 15):
    for c in range(2, 10):
        s.cell(r, c).value = None
J, I, K = f"Template!$J$3:$J${last}", f"Template!$I$3:$I${last}", f"Template!$K$3:$K${last}"
r0 = 12
for n, (m, info) in enumerate(cfg["members"].items(), start=1):
    who = f"{m} - {info['id']}"
    for k, kind in enumerate(("UI", "API")):
        r = r0 + k
        for c in range(2, 10):
            f, b, fl, al, nf = st[12 + k][c - 2]
            cell = s.cell(r, c); cell.font, cell.border, cell.fill, cell.alignment, cell.number_format = f, b, fl, al, nf
        s.cell(r, 4, kind)
        s.cell(r, 5, f"=SUM(F{r}:I{r})"); CACHED[("Summary", f"E{r}")] = count(who, kind)
        for col, stat in zip("FGHI", ("Passed", "Failed", "Blocked", "Not Executed")):
            s[f"{col}{r}"] = f'=COUNTIFS({J},{col}$11,{I},$D{r},{K},"{who}")'
            CACHED[("Summary", f"{col}{r}")] = count(who, kind, stat)
    s.cell(r0, 2, n)
    s.cell(r0, 3, f"{m} - {info['name']} ({info['id']})\n{info['modules']}")
    s.cell(r0, 3).alignment = Alignment(wrap_text=True, vertical="center")
    s.cell(r0, 2).alignment = Alignment(horizontal="center", vertical="center")
    s.merge_cells(start_row=r0, start_column=2, end_row=r0 + 1, end_column=2)
    s.merge_cells(start_row=r0, start_column=3, end_row=r0 + 1, end_column=3)
    s.row_dimensions[r0].height = s.row_dimensions[r0 + 1].height = 30
    r0 += 2
tot = r0
for c in range(2, 10):
    f, b, fl, al, nf = st[14][c - 2]
    cell = s.cell(tot, c); cell.font, cell.border, cell.fill, cell.alignment, cell.number_format = f, b, fl, al, nf
s.cell(tot, 3, "Total")
for col, stat in zip("EFGHI", (None, "Passed", "Failed", "Blocked", "Not Executed")):
    s[f"{col}{tot}"] = f"=SUM({col}12:{col}{tot - 1})"
    CACHED[("Summary", f"{col}{tot}")] = count(status=stat)
s.column_dimensions["C"].width = 60

# ---- Module Division sheet (required by the instructions, section 4.3)
md = wb.create_sheet("Module Division", 1)
head = ["Member", "Student ID", "Name", "SRS modules", "API endpoints", "API TC IDs", "UI TC IDs"]
md.append(head)
for m, info in cfg["members"].items():
    md.append([m, info["id"], info["name"], info["modules"], cfg["api_endpoints"][m],
               f"TC_API_{m}_01 - TC_API_{m}_15", f"TC_UI_{m}_01 - TC_UI_{m}_15"])
md.append([])
md.append(["Rules", "No test cases for the login function (login page, login API, logout), as instructed. "
           "Each member writes 15 API + 15 UI cases only inside their own modules; token/role checks (401/403) are "
           "written only by the member who owns that endpoint, so no scenario is duplicated."])
for c in md[1]:
    c.font = Font(bold=True)
for col, w in zip("ABCDEFG", (9, 16, 22, 55, 60, 26, 24)):
    md.column_dimensions[col].width = w
for row in md.iter_rows(min_row=2):
    for c in row:
        c.alignment = wrap
print_setup(md)
print_setup(s)

# ---- Defect Log sheet, read from the summary table in DEFECT_REPORT.md (single source)
report = os.path.join(HERE, "DEFECT_REPORT.md")
if os.path.exists(report):
    dl = wb.create_sheet("Defect Log", 2)
    dl.append(["Defect ID", "Test case", "Owner", "Defect", "Type", "SRS sentence broken", "Status"])
    for line in open(report, encoding="utf-8"):
        if line.startswith("| DEF-"):
            cells = [c.strip().replace("`", "") for c in line.strip().strip("|").split("|")]
            dl.append(cells[:6] + ["Open"])
    for c in dl[1]:
        c.font = Font(bold=True)
    for col, w in zip("ABCDEFG", (11, 15, 30, 60, 10, 60, 9)):
        dl.column_dimensions[col].width = w
    for row in dl.iter_rows(min_row=2):
        for c in row:
            c.alignment = wrap
    print_setup(dl, "1:1")

wb.calculation.fullCalcOnLoad = True  # Excel recalculates everything when the file is opened
wb.save(out)


def inject_cached_values(path, values):
    """openpyxl saves formulas without results, so previews (GitHub, phones, Protected View) show
    blanks. Write the computed result into each formula cell's <v> element."""
    import re, zipfile
    sheet_xml = {name: f"xl/worksheets/sheet{i}.xml" for i, name in enumerate(wb.sheetnames, start=1)}
    with zipfile.ZipFile(path) as z:
        files = {n: z.read(n) for n in z.namelist()}
    for (sheet, ref), val in values.items():
        name = sheet_xml[sheet]
        xml = files[name].decode("utf-8")
        pat = re.compile(r'(<c r="%s"[^>]*>)(<f>.*?</f>)(<v\s*/>|<v>.*?</v>)?' % ref)
        xml, n = pat.subn(lambda mm: f"{mm.group(1)}{mm.group(2)}<v>{val}</v>", xml, count=1)
        if not n:
            raise RuntimeError(f"formula cell {sheet}!{ref} not found")
        files[name] = xml.encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in files.items():
            z.writestr(n, data)


inject_cached_values(out, CACHED)
print(f"Wrote {out}  ({n_tc} test cases, {len(sep_rows)} member sections)")
