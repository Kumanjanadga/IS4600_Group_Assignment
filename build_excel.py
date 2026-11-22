"""Build TestCaseDocument_<Group>_v0.1.xlsx from the course template.

Reads:  template/TestCaseDocument__GroupNumber__v0.1.xlsx   (sir's template)
        results/api_results.json                          (run api-tests/run_tests.py first)
        ui-tests/ui_test_cases.py, members.json, test_index.json (portal + module of every test), DEFECT_REPORT.md
Writes: TestCaseDocument_<Group>_v0.1.xlsx

Everything is grouped by member first, then module (SRS order). IDs read Portal-Module-Type-Number, e.g. ADM-CAT-API-12.
The Tester column shows the member's name and student ID.
"""
import json, os, re, shutil, sys
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
index = json.load(open(os.path.join(HERE, "test_index.json"), encoding="utf-8"))
MODULES = index["modules"]                       # [{code, portal, module, srs}] in SRS order
TESTS = index["tests"]                           # id -> {type, member, portal, module, srs, module_code}
group = cfg["group_number"]
out = os.path.join(HERE, f"TestCaseDocument_{group}_v0.1.xlsx")
shutil.copy(os.path.join(HERE, "template", "TestCaseDocument__GroupNumber__v0.1.xlsx"), out)
STATUS = {"Pass": "Passed", "Fail": "Failed", "Blocked": "Blocked"}


def person(m):
    info = cfg["members"][m]
    return f"{info['name']} ({info['id']})"


# ---------------------------------------------------------------- collect the 180 rows
rows = []
for r in api["results"]:
    rows.append({"id": r["id"], "title": r["title"],
                 "desc": f"{r['description']}\nEndpoint: {r['endpoint']}\nRole/Token: {r['role']}",
                 "pre": r["precondition"], "steps": r["steps"], "data": r["data"], "exp": r["expected"],
                 "act": r["actual"], "type": "API", "status": STATUS[r["status"]], "member": r["member"]})
for m, cases in UI_CASES.items():
    for (tid, title, url, role, pre, steps, data, exp) in cases:
        rows.append({"id": tid, "title": title, "desc": f"{title}\nPage URL: {url}\nRole: {role}", "pre": pre,
                     "steps": steps, "data": data, "exp": exp, "act": "", "type": "UI", "status": "Not Executed",
                     "member": m})
missing = [r["id"] for r in rows if r["id"] not in TESTS]
assert not missing, f"tests missing from test_index.json: {missing}"
order = {mo["code"]: i for i, mo in enumerate(MODULES)}
for r in rows:
    t = TESTS[r["id"]]
    r.update(portal=t["portal"], module=t["module"], code=t["module_code"], srs=t["srs"],
             tester=person(r["member"]), defect=cfg["defects"].get(r["id"], ""))
MORDER = list(cfg["members"])
rows.sort(key=lambda r: (MORDER.index(r["member"]), order[r["code"]], 0 if r["type"] == "API" else 1, r["id"]))

# ---------------------------------------------------------------- Template sheet
wb = openpyxl.load_workbook(out)
ws = wb["Template"]
ws.insert_cols(2, 2)                                    # B = Portal, C = Module (after the Test Identifier)
for col, head in ((2, "Portal"), (3, "Module")):
    h = ws.cell(row=2, column=col, value=head)
    src = ws.cell(row=2, column=1)
    h.font, h.border, h.fill, h.alignment = copy(src.font), copy(src.border), copy(src.fill), copy(src.alignment)
NCOL = 14
styles = []
for c in range(1, NCOL + 1):
    src = ws.cell(row=3, column=1 if c in (2, 3) else c)
    styles.append((copy(src.font), copy(src.border), copy(src.fill)))
ws.delete_rows(3, ws.max_row)
wrap = Alignment(wrap_text=True, vertical="top")
thick = Side(style="medium")
COLS = ["id", "portal", "module", "title", "desc", "pre", "steps", "data", "exp", "act", "type", "status", "tester", "defect"]

i, cur_member, cur_code, sections = 3, None, None, 0


def header(row_i, text, size, height):
    ws.cell(row=row_i, column=1, value=text)
    ws.merge_cells(start_row=row_i, start_column=1, end_row=row_i, end_column=NCOL)
    ws.cell(row=row_i, column=1).font = Font(bold=True, size=size)
    ws.cell(row=row_i, column=1).alignment = Alignment(vertical="center")
    side = thick if size >= 14 else Side(style="thin")
    for c in range(1, NCOL + 1):
        ws.cell(row=row_i, column=c).border = Border(top=side, bottom=side, left=side if c == 1 else None,
                                                     right=side if c == NCOL else None)
    ws.row_dimensions[row_i].height = height


for r in rows:
    if r["member"] != cur_member:                        # member section (each member starts a new printed page)
        mine = [x for x in rows if x["member"] == r["member"]]
        mods = []
        for x in mine:
            if x["module"] not in mods:
                mods.append(x["module"])
        if cur_member is not None:
            ws.row_breaks.append(Break(id=i - 1))
        header(i, f"{r['tester']}   |   {', '.join(mods)}   |   "
                  f"{sum(1 for x in mine if x['type'] == 'API')} API + {sum(1 for x in mine if x['type'] == 'UI')} UI test cases",
               15, 30)
        cur_member, cur_code, sections = r["member"], None, sections + 1
        i += 1
    if r["code"] != cur_code:                            # module sub-section inside the member
        sub = [x for x in rows if x["member"] == r["member"] and x["code"] == r["code"]]
        header(i, f"{r['portal']}  ·  {r['module']} (SRS {r['srs']})   -   "
                  f"{sum(1 for x in sub if x['type'] == 'API')} API + {sum(1 for x in sub if x['type'] == 'UI')} UI",
               12, 22)
        cur_code = r["code"]
        i += 1
    for c, key in enumerate(COLS, start=1):
        cell = ws.cell(row=i, column=c, value=r[key])
        f, b, fl = styles[c - 1]
        cell.font, cell.border, cell.fill, cell.alignment = f, b, fl, wrap
        if key == "status" and r[key] == "Failed":
            cell.font = Font(bold=True)                  # bold instead of colour (printed in black & white)
    i += 1
last = i - 1
for col, w in zip("ABCDEFGHIJKLMN", (17, 11, 18, 32, 38, 28, 40, 32, 40, 40, 7, 12, 22, 10)):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "D3"
ws.auto_filter.ref = f"A2:N{last}"
ws.data_validations.dataValidation = []
dv1 = DataValidation(type="list", formula1='"Passed,Failed,Blocked,Not Executed"', allow_blank=True)
dv2 = DataValidation(type="list", formula1='"UI,API"', allow_blank=True)
dv1.add(f"L3:L{last}"); dv2.add(f"K3:K{last}")
ws.add_data_validation(dv1); ws.add_data_validation(dv2)


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

# ---------------------------------------------------------------- Summary sheet (Feature = module)
s = wb["Summary"]
s["C3"] = "QA Training App - Admin App, Client App and Backend API (all modules)"
s["C4"] = "v0.1"
s["E4"] = "16/11/2026"
s["G4"] = date.today().strftime("%d/%m/%Y")
s["C5"] = "QA_Training_App_SRS_v2.1.pdf"
s["C6"] = "Swagger / OpenAPI (http://localhost:8080/swagger-ui.html)"
s["C8"] = "v0.1"
s["D8"] = f"{group} (all members)"
s["E8"] = (f"Test case design: {len(rows)} test cases (15 API + 15 UI per member), no login cases. "
           f"API cases executed on {api['executed_at'][:10]}; UI not executed (no UI in this release). "
           f"{len(cfg['defects'])} defects - see the Defect Log sheet.")
CACHED = {}  # (sheet, cell) -> computed value, written next to each formula so viewers show numbers


def count(module=None, kind=None, status=None, tester=None):
    return sum(1 for r in rows if (module is None or r["module"] == module) and (kind is None or r["type"] == kind)
               and (status is None or r["status"] == status) and (tester is None or r["tester"] == tester))


st = {r: [(copy(s.cell(r, c).font), copy(s.cell(r, c).border), copy(s.cell(r, c).fill),
           copy(s.cell(r, c).alignment), s.cell(r, c).number_format) for c in range(2, 10)] for r in (12, 13, 14)}
for rng_ in list(s.merged_cells.ranges):
    if rng_.min_row >= 12:
        s.unmerge_cells(str(rng_))
for r in range(12, 15):
    for c in range(2, 10):
        s.cell(r, c).value = None
STA, TYP, MOD, TST = (f"Template!$L$3:$L${last}", f"Template!$K$3:$K${last}", f"Template!$C$3:$C${last}",
                      f"Template!$M$3:$M${last}")
features = []                                            # (tester, module record) in member -> module order
for r in rows:
    key = (r["tester"], r["code"])
    if key not in [(f[0], f[1]["code"]) for f in features]:
        features.append((r["tester"], next(mo for mo in MODULES if mo["code"] == r["code"])))
r0 = 12
for n, (who, mo) in enumerate(features, start=1):
    for k, kind in enumerate(("UI", "API")):
        r = r0 + k
        for c in range(2, 10):
            f, b, fl, al, nf = st[12 + k][c - 2]
            cell = s.cell(r, c); cell.font, cell.border, cell.fill, cell.alignment, cell.number_format = f, b, fl, al, nf
        s.cell(r, 4, kind)
        s.cell(r, 5, f"=SUM(F{r}:I{r})"); CACHED[("Summary", f"E{r}")] = count(mo["module"], kind, tester=who)
        for col, stat in zip("FGHI", ("Passed", "Failed", "Blocked", "Not Executed")):
            s[f"{col}{r}"] = f'=COUNTIFS({STA},{col}$11,{TYP},$D{r},{MOD},"{mo["module"]}",{TST},"{who}")'
            CACHED[("Summary", f"{col}{r}")] = count(mo["module"], kind, stat, tester=who)
    s.cell(r0, 2, n)
    s.cell(r0, 3, f"{who}\n{mo['portal']} · {mo['module']} (SRS {mo['srs']})")
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
s.column_dimensions["C"].width = 62

# ---------------------------------------------------------------- Module Division sheet (required by the instructions)
def id_ranges(ids):
    """Compress e.g. ADM-CAT-API-01..14 into 'ADM-CAT-API-01 – 14'."""
    by = {}
    for t in ids:
        pre, num = t.rsplit("-", 1)
        by.setdefault(pre, []).append(int(num))
    parts = []
    for pre, nums in by.items():
        nums.sort(); runs, start, prev = [], nums[0], nums[0]
        for x in nums[1:] + [None]:
            if x is not None and x == prev + 1:
                prev = x; continue
            runs.append(f"{start:02d}" if start == prev else f"{start:02d}–{prev:02d}")
            if x is not None:
                start = prev = x
        parts.append(f"{pre}-{', '.join(runs)}")
    return "\n".join(parts)


md = wb.create_sheet("Module Division", 1)
md.append(["Member", "Student ID", "Portal · Modules", "API test cases", "UI test cases", "Defects"])
for m, info in cfg["members"].items():
    mine = [r for r in rows if r["member"] == m]
    mods = []
    for r in mine:
        lab = f"{r['portal']} · {r['module']}"
        if lab not in mods:
            mods.append(lab)
    defs = sorted(cfg["defects"][r["id"]] for r in mine if r["id"] in cfg["defects"])
    md.append([info["name"], info["id"], "\n".join(mods),
               f"{sum(1 for r in mine if r['type'] == 'API')}:\n" + id_ranges([r["id"] for r in mine if r["type"] == "API"]),
               f"{sum(1 for r in mine if r['type'] == 'UI')}:\n" + id_ranges([r["id"] for r in mine if r["type"] == "UI"]),
               ", ".join(defs)])
md.append([])
hdr2 = md.max_row + 1
md.append(["Portal", "Module (SRS)", "Tester", "API", "UI", "Defects"])
for mo in MODULES:
    mine = [r for r in rows if r["code"] == mo["code"]]
    owners = []
    for r in mine:
        if r["tester"] not in owners:
            owners.append(r["tester"])
    md.append([mo["portal"], f"{mo['module']} ({mo['srs']})", ", ".join(owners),
               sum(1 for r in mine if r["type"] == "API"), sum(1 for r in mine if r["type"] == "UI"),
               ", ".join(sorted(r["defect"] for r in mine if r["defect"])) or "-"])
md.append([])
md.append(["Test case ID", "Portal-Module-Type-Number, e.g. ADM-CAT-API-12 = Admin App, Category Management, API case 12. "
           "ADM = Admin App, CLI = Client App, API = Backend API (general rules)."])
md.append(["Rules", "No test cases for the login function (login page, login API, logout), as instructed. "
           "Each member writes 15 API + 15 UI cases inside their own modules; token/role checks (401/403) are written only "
           "by the member who owns that endpoint, so no scenario is duplicated."])
for c in list(md[1]) + list(md[hdr2]):
    c.font = Font(bold=True)
for col, w in zip("ABCDEF", (26, 22, 44, 42, 42, 26)):
    md.column_dimensions[col].width = w
for row in md.iter_rows(min_row=2):
    for c in row:
        c.alignment = wrap
print_setup(md)
print_setup(s)

# ---------------------------------------------------------------- Defect Log sheet (from DEFECT_REPORT.md)
report = os.path.join(HERE, "DEFECT_REPORT.md")
dl = wb.create_sheet("Defect Log", 2)
dl.append(["Defect ID", "Tester", "Portal", "Module", "Test case", "Defect", "Type", "SRS sentence broken", "Status"])
n_def = 0
for line in open(report, encoding="utf-8"):
    if re.match(r"\| DEF-\d{3} \|", line):
        d, pm, tc, text, typ, owner, srs = [c.strip().replace("`", "") for c in line.strip().strip("|").split("|")][:7]
        portal, module = [x.strip() for x in pm.split("·")]
        dl.append([d, owner, portal, module, tc, text, typ, srs, "Open"]); n_def += 1
assert n_def == len(cfg["defects"]), (n_def, len(cfg["defects"]))
for c in dl[1]:
    c.font = Font(bold=True)
for col, w in zip("ABCDEFGHI", (10, 26, 12, 22, 16, 50, 9, 55, 8)):
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
    import zipfile
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
print(f"Wrote {out}  ({len(rows)} test cases, {sections} member sections, {len(features)} member-module features, {n_def} defects)")
