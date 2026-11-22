"""Build the printable hand-in PDF: TestCaseDocument_Group20.pdf

Black and white, A4 landscape, no cover page (sir's rule). Everything is grouped by member, then module.
Reads the same files as build_excel.py, so the PDF and the Excel always match.
"""
import json, os, re, sys
from datetime import date
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (CondPageBreak, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ui-tests"))
from ui_test_cases import UI_CASES  # noqa: E402

FONTS = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Body", os.path.join(FONTS, "arial.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", os.path.join(FONTS, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Sym", os.path.join(FONTS, "seguisym.ttf")))   # only for the few emoji in test data
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")
ARIAL = TTFont("ArialCheck", os.path.join(FONTS, "arial.ttf")).face.charToGlyph

cfg = json.load(open(os.path.join(HERE, "members.json"), encoding="utf-8"))
api = json.load(open(os.path.join(HERE, "results", "api_results.json"), encoding="utf-8"))
index = json.load(open(os.path.join(HERE, "test_index.json"), encoding="utf-8"))
MODULES, TESTS = index["modules"], index["tests"]
GROUP_NO = re.sub(r"\D", "", cfg["group_number"]) or cfg["group_number"]
OUT = os.path.join(HERE, f"TestCaseDocument_Group{GROUP_NO}.pdf")
BLACK = colors.black

# ------------------------------------------------------------------ text helpers
def esc(text):
    """Escape for reportlab markup, keep line breaks, and switch font for characters Arial can't draw."""
    text = "" if text is None else str(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = "".join(f'<font name="Sym">{ch}</font>' if ord(ch) > 0xFFFF or (ord(ch) > 126 and ord(ch) not in ARIAL) else ch
                   for ch in text)
    return text.replace("\n", "<br/>")


def short_actual(actual, status):
    """Turn the runner's log line into a short, readable actual result."""
    if not actual:
        return "-"
    base, _, mismatch = actual.partition(" | MISMATCH: ")
    code = base.split(",", 1)[0].strip()
    if "<!doctype html" in base.lower() or "<html" in base.lower():
        text = f"{code} - an HTML error page was returned (not JSON)"
    else:
        msg = re.search(r"message='(.*?)'", base)
        errs = re.search(r"errors=(\{.*\})", base)
        text = f"{code} - {msg.group(1)}" if msg else base
        if errs:
            try:
                e = json.loads(errs.group(1))
                text += ". " + "; ".join(f"{k}: {v}" for k, v in e.items())
            except ValueError:
                pass
    if status == "Fail" and mismatch:
        # status / message / field differences are already visible in the line above; keep only the plain checks
        notes = [m.replace("check failed: ", "").strip() for m in mismatch.split("; ")
                 if m.startswith("check failed: ")]
        notes = [re.sub(r"^exactly one 201 \(got \[(.*)\]\)$",
                        lambda g: f"expected one 201, got {g.group(1).count('201')} x 201", n) for n in notes]
        notes = [re.sub(r"\(got \[(.*?)\]\)", lambda g: "(got " + g.group(1) + ")", n) for n in notes]
        if notes:
            text += "\n" + "; ".join(n[0].upper() + n[1:] for n in notes) + "."
    return text


def plain_steps(steps, endpoint):
    """The runner's default 3-step text is wordy; say the same thing in two plain steps."""
    m = re.match(r"1\. Send (\S+ \S+) using (.+?)\.\n2\. Send the test data as the request\.\n"
                 r"3\. Check the HTTP status code and the response body\.$", steps)
    if m:
        return f"1. Send {m.group(1)} with the test data ({m.group(2)}).\n2. Check the status code and the response."
    return steps


def plain_defect(text):
    return text.replace("→ both", "- both").replace(" → ", " gives error ").replace("error 500", "error 500")


def person(m):
    i = cfg["members"][m]
    return f"{i['name']} ({i['id']})"


# ------------------------------------------------------------------ rows (same data as the Excel)
rows = []
for r in api["results"]:
    rows.append({"id": r["id"], "type": "API", "member": r["member"], "title": r["title"],
                 "where": f"{r['endpoint']}\nRole: {r['role']}", "pre": r["precondition"], "steps": r["steps"],
                 "data": r["data"], "exp": r["expected"], "act": short_actual(r["actual"], r["status"]),
                 "steps": plain_steps(r["steps"], r["endpoint"]),
                 "status": {"Pass": "Passed", "Fail": "Failed", "Blocked": "Blocked"}[r["status"]]})
for m, cases in UI_CASES.items():
    for (tid, title, url, role, pre, steps, data, exp) in cases:
        rows.append({"id": tid, "type": "UI", "member": m, "title": title, "where": f"Page: {url}\nRole: {role}",
                     "pre": pre, "steps": steps, "data": data, "exp": exp, "act": "", "status": "Not Executed"})
modorder = {mo["code"]: i for i, mo in enumerate(MODULES)}
MORDER = list(cfg["members"])
for r in rows:
    t = TESTS[r["id"]]
    r.update(code=t["module_code"], portal=t["portal"], module=t["module"], srs=t["srs"],
             defect=cfg["defects"].get(r["id"], ""))
rows.sort(key=lambda r: (MORDER.index(r["member"]), modorder[r["code"]], 0 if r["type"] == "API" else 1, r["id"]))

defects = []
for line in open(os.path.join(HERE, "DEFECT_REPORT.md"), encoding="utf-8"):
    if re.match(r"\| DEF-\d{3} \|", line):
        d, pm, tc, text, typ, owner, srs = [c.strip().replace("`", "") for c in line.strip().strip("|").split("|")][:7]
        defects.append({"id": d, "module": pm.replace(" · ", " - "), "test": tc, "text": plain_defect(text),
                        "how": "One request" if typ == "Single" else "Same request sent together", "owner": owner,
                        "srs": srs, "member": TESTS[tc]["member"]})

# ------------------------------------------------------------------ styles (black and white)
base = ParagraphStyle("base", fontName="Body", fontSize=8, leading=10, alignment=TA_LEFT, textColor=BLACK)
cell = ParagraphStyle("cell", parent=base, fontSize=7.6, leading=9.4)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Body-Bold")
head = ParagraphStyle("head", parent=cell, fontName="Body-Bold")
h_title = ParagraphStyle("t", parent=base, fontName="Body-Bold", fontSize=15, leading=19)
h_group = ParagraphStyle("g", parent=base, fontName="Body-Bold", fontSize=22, leading=26)
h_member = ParagraphStyle("hm", parent=base, fontName="Body-Bold", fontSize=14, leading=18, spaceAfter=2)
h_module = ParagraphStyle("hmod", parent=base, fontName="Body-Bold", fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=3)
h_type = ParagraphStyle("htype", parent=base, fontName="Body-Bold", fontSize=8.5, leading=11, spaceBefore=3, spaceAfter=2)
note = ParagraphStyle("note", parent=base, fontSize=8.5, leading=11.5)


def P(text, style=cell):
    return Paragraph(esc(text), style)


def grid(data, widths, header_rows=1, bold_first_col=False):
    t = Table(data, colWidths=widths, repeatRows=header_rows)
    style = [("GRID", (0, 0), (-1, -1), 0.5, BLACK),
             ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 1.3, BLACK),
             ("BOX", (0, 0), (-1, -1), 1, BLACK),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
             ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    t.setStyle(TableStyle(style))
    return t


class NumberedCanvas(canvas.Canvas):
    """Footer with 'Page x of y' on every page."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            w, h = self._pagesize
            self.setFont("Body", 7.5)
            self.setLineWidth(0.5)
            self.line(12 * mm, 10 * mm, w - 12 * mm, 10 * mm)
            self.drawString(12 * mm, 6.5 * mm, f"IS4600 IT Quality Assurance  |  Task 1: Test Case Design  |  Group {GROUP_NO}")
            self.drawRightString(w - 12 * mm, 6.5 * mm, f"Page {self._pageNumber} of {total}")
            super().showPage()
        super().save()


# ------------------------------------------------------------------ document
PAGE = landscape(A4)
W = PAGE[0] - 24 * mm
story = []

# first page: plain header block (no cover page)
story.append(Paragraph("IS4600 IT Quality Assurance - Group Assignment", h_title))
story.append(Paragraph("Task 1: Test Case Design  -  QA Training App", h_title))
story.append(Spacer(1, 4))
story.append(Paragraph(f"Group No: {GROUP_NO}", h_group))
story.append(Spacer(1, 4))
n_api = sum(1 for r in rows if r["type"] == "API"); n_ui = len(rows) - n_api
passed = sum(1 for r in rows if r["status"] == "Passed"); failed = sum(1 for r in rows if r["status"] == "Failed")
story.append(Paragraph(esc(
    f"Reference documents: QA_Training_App_SRS_v2.1, Deployment Guide, Swagger (http://localhost:8080/swagger-ui.html). "
    f"API test cases were run on {api['executed_at'][:10]}. The UI is not part of this release, so the UI test cases were "
    f"written from the SRS and are not executed yet. As instructed, there are no test cases for the login function."), note))
story.append(Spacer(1, 8))

story.append(Paragraph("Members and module division", h_module))
md = [[P("Member", head), P("Student ID", head), P("Modules (SRS section)", head), P("API", head), P("UI", head),
       P("Defects found", head)]]
for m, info in cfg["members"].items():
    mine = [r for r in rows if r["member"] == m]
    mods = []
    for r in mine:
        lab = f"{r['portal']} - {r['module']} ({r['srs']})"
        if lab not in mods:
            mods.append(lab)
    defs = ", ".join(d["id"] for d in defects if d["member"] == m)
    md.append([P(info["name"], cellb), P(info["id"]), P("\n".join(mods)), P(sum(1 for r in mine if r["type"] == "API")),
               P(sum(1 for r in mine if r["type"] == "UI")), P(defs)])
story.append(grid(md, [W * .17, W * .09, W * .44, W * .05, W * .05, W * .20]))
story.append(Spacer(1, 8))

story.append(Paragraph("Summary", h_module))
sm = [[P("Test cases", head), P("Total", head), P("Passed", head), P("Failed", head), P("Not executed", head)],
      [P("API test cases (run against the application)"), P(n_api), P(passed), P(failed), P(0)],
      [P("UI test cases (written from the SRS)"), P(n_ui), P(0), P(0), P(n_ui)],
      [P("Total", cellb), P(len(rows), cellb), P(passed, cellb), P(failed, cellb), P(n_ui, cellb)]]
story.append(grid(sm, [W * .40, W * .10, W * .10, W * .10, W * .12]))
story.append(Spacer(1, 6))
story.append(Paragraph(esc(
    f"{failed} API test cases failed. Each failure is a defect where the application does not follow the SRS; they are "
    f"listed at the end (DEF-001 to DEF-{len(defects):03d})."), note))
story.append(Spacer(1, 4))
story.append(Paragraph(esc(
    "How to read a test case ID: ADM-CAT-API-12 means Admin App, Category Management, API test case 12. "
    "ADM = Admin App, CLI = Client App, API = rules that apply to every API. The Tester is the member who wrote the case."), note))

# one section per member, then module, then API / UI tables
API_W = [W * x for x in (.092, .11, .12, .09, .135, .115, .148, .13, .06)]
UI_W = [W * x for x in (.092, .13, .115, .115, .165, .125, .198, .06)]
for m, info in cfg["members"].items():
    mine = [r for r in rows if r["member"] == m]
    story.append(PageBreak())
    mods = []
    for r in mine:
        if r["module"] not in mods:
            mods.append(r["module"])
    defs = ", ".join(d["id"] for d in defects if d["member"] == m) or "none"
    story.append(Paragraph(esc(f"Tester: {info['name']}  ({info['id']})"), h_member))
    story.append(Paragraph(esc(f"Modules: {', '.join(mods)}   |   "
                               f"{sum(1 for r in mine if r['type'] == 'API')} API and "
                               f"{sum(1 for r in mine if r['type'] == 'UI')} UI test cases   |   Defects: {defs}"), note))
    for code in [c for c in dict.fromkeys(r["code"] for r in mine)]:
        sub = [r for r in mine if r["code"] == code]
        first = sub[0]
        story.append(CondPageBreak(60 * mm))
        story.append(Paragraph(esc(f"{first['portal']} - {first['module']} (SRS {first['srs']})"), h_module))
        api_rows = [r for r in sub if r["type"] == "API"]
        ui_rows = [r for r in sub if r["type"] == "UI"]
        if api_rows:
            story.append(Paragraph(f"API test cases ({len(api_rows)})", h_type))
            data = [[P(x, head) for x in ("Test case ID", "Test title", "Endpoint and role", "Precondition", "Test steps",
                                          "Test data", "Expected result", "Actual result", "Status")]]
            for r in api_rows:
                status = r["status"] + (f"\n{r['defect']}" if r["defect"] else "")
                data.append([P(r["id"], cellb), P(r["title"]), P(r["where"]), P(r["pre"]), P(r["steps"]), P(r["data"]),
                             P(r["exp"]), P(r["act"]), P(status, cellb if r["defect"] else cell)])
            story.append(grid(data, API_W))
        if ui_rows:
            story.append(Paragraph(f"UI test cases ({len(ui_rows)})", h_type))
            data = [[P(x, head) for x in ("Test case ID", "Test title", "Page and role", "Precondition", "Test steps",
                                          "Test data", "Expected result", "Status")]]
            for r in ui_rows:
                data.append([P(r["id"], cellb), P(r["title"]), P(r["where"]), P(r["pre"]), P(r["steps"]), P(r["data"]),
                             P(r["exp"]), P(r["status"])])
            story.append(grid(data, UI_W))

# defects, grouped by member
story.append(PageBreak())
story.append(Paragraph("Defects found", h_member))
story.append(Paragraph(esc(
    "Each defect is a place where the application does not do what the SRS says. \"One request\" means it can be repeated "
    "with a single request in Swagger. \"Same request sent together\" means the same request is sent several times at the "
    "same moment (Postman Collection Runner, several iterations, no delay). Full steps are in DEFECT_REPORT.md."), note))
DW = [W * x for x in (.065, .15, .105, .27, .10, .31)]
for m, info in cfg["members"].items():
    mine = [d for d in defects if d["member"] == m]
    if not mine:
        continue
    block = [Paragraph(esc(f"{info['name']}  ({info['id']})"), h_module)]
    data = [[P(x, head) for x in ("Defect", "Module", "Test case", "What is wrong", "How to repeat", "SRS rule broken")]]
    for d in mine:
        data.append([P(d["id"], cellb), P(d["module"]), P(d["test"]), P(d["text"]), P(d["how"]), P(d["srs"])])
    block.append(grid(data, DW))
    story.append(KeepTogether(block))

doc = SimpleDocTemplate(OUT, pagesize=PAGE, leftMargin=12 * mm, rightMargin=12 * mm, topMargin=11 * mm,
                        bottomMargin=14 * mm, title=f"IS4600 Task 1 - Test Case Document - Group {GROUP_NO}",
                        author=f"Group {GROUP_NO}")
doc.build(story, canvasmaker=NumberedCanvas)
print(f"Wrote {OUT}")
