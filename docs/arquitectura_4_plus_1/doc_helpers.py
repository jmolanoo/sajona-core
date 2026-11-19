"""Utilidades strictly B&W (#000000 / #FFFFFF) para el Documento 4+1 de SAJONA Núcleo."""

from pathlib import Path
from PIL import Image
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

DIAGRAMS_PNG = Path("/home/molano/sajona-core/docs/diagrams/png")
BLACK = RGBColor(0x00, 0x00, 0x00)
FONT_NAME = "Liberation Serif"
FONT_SANS = "Liberation Sans"


def set_cell_margins(cell, top=80, bottom=80, left=110, right=110):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_bw_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:left w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        '<w:right w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        "</w:tblBorders>"
    )
    tblPr.append(borders)


def add_field(run, field_text: str):
    for chunk in (
        f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>',
        f'<w:instrText {nsdecls("w")} xml:space="preserve"> {field_text} </w:instrText>',
        f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>',
        f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>',
    ):
        run._r.append(parse_xml(chunk))


def configure_styles(doc: Document):
    normal = doc.styles["Normal"]
    normal.font.name = FONT_NAME
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = BLACK
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(5)

    for level, size, before, after in (
        ("Heading 1", 14.5, 14, 5),
        ("Heading 2", 12, 10, 4),
        ("Heading 3", 10.5, 8, 3),
    ):
        st = doc.styles[level]
        st.font.name = FONT_SANS
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = BLACK
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True


def add_header_footer(doc: Document):
    sec = doc.sections[0]
    sec.top_margin = Inches(0.85)
    sec.bottom_margin = Inches(0.8)
    sec.left_margin = Inches(0.9)
    sec.right_margin = Inches(0.9)
    sec.different_first_page_header_footer = True

    hdr = sec.header.paragraphs[0]
    hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rh = hdr.add_run("SAJONA ADE — Arquitectura 4+1 Núcleo Productivo (Módulos 1–3 + Dashboard)")
    rh.font.name = FONT_SANS
    rh.font.size = Pt(8.5)
    rh.font.color.rgb = BLACK

    ftr = sec.footer.paragraphs[0]
    ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for txt, fld in (
        ("Universidad Surcolombiana (USCO) — Ingeniería de Software   |   Página ", None),
        (None, "PAGE"),
        (" de ", None),
        (None, "NUMPAGES"),
    ):
        r = ftr.add_run(txt or "")
        r.font.name = FONT_SANS
        r.font.size = Pt(8.5)
        r.font.color.rgb = BLACK
        if fld:
            add_field(r, fld)


def add_p(doc: Document, text: str = "", bold_prefix: str = ""):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = FONT_NAME
        rb.font.size = Pt(10.5)
        rb.font.color.rgb = BLACK
    if text:
        r = p.add_run(text)
        r.font.name = FONT_NAME
        r.font.size = Pt(10.5)
        r.font.color.rgb = BLACK
    return p


def add_bullets(doc: Document, items: list[tuple[str, str]]):
    for label, desc in items:
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(2.5)
        if label:
            rl = p.add_run(label + " ")
            rl.bold = True
            rl.font.name = FONT_NAME
            rl.font.size = Pt(10)
            rl.font.color.rgb = BLACK
        rd = p.add_run(desc)
        rd.font.name = FONT_NAME
        rd.font.size = Pt(10)
        rd.font.color.rgb = BLACK


def add_numbered(doc: Document, items: list[tuple[str, str]]):
    for label, desc in items:
        p = doc.add_paragraph(style="List Number")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(2.5)
        if label:
            rl = p.add_run(label + " ")
            rl.bold = True
            rl.font.name = FONT_NAME
            rl.font.size = Pt(10)
            rl.font.color.rgb = BLACK
        rd = p.add_run(desc)
        rd.font.name = FONT_NAME
        rd.font.size = Pt(10)
        rd.font.color.rgb = BLACK


def add_bw_table(
    doc: Document,
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[float] | None = None,
    caption: str | None = None,
):
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.keep_with_next = True
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(3)
        rc = cp.add_run(caption)
        rc.bold = True
        rc.font.name = FONT_SANS
        rc.font.size = Pt(9.5)
        rc.font.color.rgb = BLACK

    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_bw_borders(tbl)

    hdr_row = tbl.rows[0]
    hdr_row._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    hdr_row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    for idx, text in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(cell, 90, 90, 100, 100)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(text)
        r.bold = True
        r.font.name = FONT_SANS
        r.font.size = Pt(9)
        r.font.color.rgb = BLACK
        if col_widths:
            cell.width = Inches(col_widths[idx])

    for r_i, row_data in enumerate(rows):
        row = tbl.rows[r_i + 1]
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for c_i, val in enumerate(row_data):
            cell = row.cells[c_i]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            set_cell_margins(cell, 70, 70, 100, 100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            r = p.add_run(val)
            r.font.name = FONT_NAME
            r.font.size = Pt(9)
            r.font.color.rgb = BLACK
            if col_widths:
                cell.width = Inches(col_widths[c_i])

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(3)


def add_diagram(doc: Document, filename: str, fig_num: str, title: str, explanation: str):
    img_path = DIAGRAMS_PNG / filename
    with Image.open(img_path) as im:
        px_w, px_h = im.size
    max_w = 6.3
    max_h = 5.2
    aspect = px_h / px_w
    width = max_w
    height = width * aspect
    if height > max_h:
        height = max_h
        width = height / aspect

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.keep_with_next = True
    p_img.paragraph_format.space_before = Pt(5)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.add_run().add_picture(str(img_path), width=Inches(width), height=Inches(height))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.keep_with_next = bool(explanation)
    p_cap.paragraph_format.space_after = Pt(4)
    rc = p_cap.add_run(f"{fig_num}. {title}")
    rc.bold = True
    rc.italic = True
    rc.font.name = FONT_SANS
    rc.font.size = Pt(9)
    rc.font.color.rgb = BLACK

    if explanation:
        add_p(doc, explanation)


def add_dotted_index_line(doc: Document, label: str, page_str: str, indent: float = 0.0, bold: bool = False, size: float = 9.5):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(indent)
    p.paragraph_format.space_before = Pt(1.5 if bold else 0.8)
    p.paragraph_format.space_after = Pt(1.5 if bold else 0.8)
    p.paragraph_format.line_spacing = 1.02
    p.paragraph_format.tab_stops.add_tab_stop(
        Inches(6.65), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
    )
    rl = p.add_run(label)
    rl.font.name = FONT_SANS if bold else FONT_NAME
    rl.font.size = Pt(size)
    rl.bold = bold
    rl.font.color.rgb = BLACK

    rt = p.add_run("\t")
    rt.font.size = Pt(size)

    rp = p.add_run(page_str)
    rp.font.name = FONT_SANS if bold else FONT_NAME
    rp.font.size = Pt(size)
    rp.bold = bold
    rp.font.color.rgb = BLACK
