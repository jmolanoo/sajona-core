"""Generador iterativo B&N (2+ pasadas) del Documento de Arquitectura 4+1 SAJONA Núcleo."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import fitz
from docx import Document
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from doc_helpers import add_header_footer, configure_styles  # noqa: E402
from doc_sections_closing import populate_closing_sections  # noqa: E402
from doc_sections_global import (  # noqa: E402
    FIG_TITLES,
    TBL_TITLES,
    TOC_TITLES,
    build_cover,
    build_toc_and_indices,
    populate_global_sections,
)
from doc_sections_modules import populate_module_sections  # noqa: E402

DOCX_OUT = HERE / "SAJONA_Core_Documento_Arquitectura_4_mas_1.docx"
PDF_OUT = HERE / "SAJONA_Core_Documento_Arquitectura_4_mas_1.pdf"
ASR_P95_STR = "p95=7.41 ms origen / 315.18 ms HTTPS; 0 errores"

FORBIDDEN_TERMS = (
    "chatgpt",
    "openai",
    "claude",
    "anthropic",
    "gemini",
    "antigravity",
    "copilot",
    "large language model",
    "llm",
    "inteligencia artificial",
    "ia generativa",
    "prompt",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def render_once(
    toc_pages: dict[str, int] | None,
    fig_pages: dict[str, int] | None,
    tbl_pages: dict[str, int] | None,
) -> None:
    doc = Document()
    configure_styles(doc)
    add_header_footer(doc)
    build_cover(doc)
    build_toc_and_indices(doc, toc_pages, fig_pages, tbl_pages)
    populate_global_sections(doc, ASR_P95_STR)
    populate_module_sections(doc)
    populate_closing_sections(doc)
    doc.save(str(DOCX_OUT))

    cmd = [
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(HERE),
        str(DOCX_OUT),
    ]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    if not PDF_OUT.exists():
        raise RuntimeError(f"LibreOffice no generó {PDF_OUT}: {res.stdout} {res.stderr}")


def _find_body_start(pages_text: list[str]) -> int:
    for i in range(1, len(pages_text)):
        t = pages_text[i]
        if (
            "Tabla de Contenido" not in t
            and "Índice de Figuras y Tablas" not in t
            and "1. Introducción" in t
            and "....." not in t
        ):
            return i
    raise RuntimeError("No se pudo localizar la página inicial del cuerpo ('1. Introducción').")


def scan_pdf_pages() -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    pdf = fitz.open(str(PDF_OUT))
    pages_norm = [_norm(p.get_text("text")) for p in pdf]
    body_start = _find_body_start(pages_norm)

    toc_pages: dict[str, int] = {}
    search_from = body_start
    for _lvl, title in TOC_TITLES:
        target = _norm(title)
        pattern = re.compile(r"(?:^|\s)" + re.escape(target) + r"(?:\s|$)")
        found = None
        for i in range(search_from, len(pages_norm)):
            if pattern.search(pages_norm[i]):
                found = i + 1
                search_from = i
                break
        if found is None:
            for i in range(body_start, len(pages_norm)):
                if pattern.search(pages_norm[i]):
                    found = i + 1
                    break
        if found is None:
            raise RuntimeError(f"Encabezado no localizado en PDF: {title}")
        toc_pages[title] = found

    fig_pages: dict[str, int] = {}
    for ft in FIG_TITLES:
        target = _norm(ft)
        found = None
        for i in range(body_start, len(pages_norm)):
            if target in pages_norm[i]:
                found = i + 1
                break
        if found is None:
            raise RuntimeError(f"Figura no localizada en PDF: {ft}")
        fig_pages[ft] = found

    tbl_pages: dict[str, int] = {}
    for tt in TBL_TITLES:
        target = _norm(tt)
        found = None
        for i in range(body_start, len(pages_norm)):
            if target in pages_norm[i]:
                found = i + 1
                break
        if found is None:
            raise RuntimeError(f"Tabla no localizada en PDF: {tt}")
        tbl_pages[tt] = found

    pdf.close()
    return toc_pages, fig_pages, tbl_pages


def verify_bw_and_clean_pdf(preview_dir: Path) -> int:
    pdf = fitz.open(str(PDF_OUT))
    total_pages = len(pdf)
    preview_dir.mkdir(parents=True, exist_ok=True)
    for f in preview_dir.glob("*.png"):
        f.unlink()

    sample_pages = {0, 1, 2, 3, 6, 13, 20, 27, total_pages - 3, total_pages - 1}
    for idx, page in enumerate(pdf):
        raw = page.get_text("text").lower()
        for term in FORBIDDEN_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", raw):
                raise RuntimeError(f"Término prohibido detectado en pág. {idx + 1}: {term}")

        pix = page.get_pixmap(dpi=100)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        r_band = im.getdata(0)
        g_band = im.getdata(1)
        b_band = im.getdata(2)
        for r, g, b in zip(r_band, g_band, b_band):
            if r != g or g != b:
                raise RuntimeError(
                    f"Píxel con color detectado en pág. {idx + 1}: RGB=({r},{g},{b})"
                )
        if idx in sample_pages:
            im.save(str(preview_dir / f"page_{idx + 1:02d}.png"))

    pdf.close()
    return total_pages


def main():
    toc_pages: dict[str, int] | None = None
    fig_pages: dict[str, int] | None = None
    tbl_pages: dict[str, int] | None = None

    for pass_num in range(1, 6):
        render_once(toc_pages, fig_pages, tbl_pages)
        new_toc, new_fig, new_tbl = scan_pdf_pages()
        if (new_toc, new_fig, new_tbl) == (toc_pages, fig_pages, tbl_pages):
            print(f"[OK] Índices convergieron exactamente en pasada {pass_num}.")
            break
        toc_pages, fig_pages, tbl_pages = new_toc, new_fig, new_tbl
        print(f"[Pasada {pass_num}] Índices actualizados ({len(toc_pages)} secs, {len(fig_pages)} figs, {len(tbl_pages)} tbls).")
    else:
        render_once(toc_pages, fig_pages, tbl_pages)
        print("[WARN] Convergencia forzada tras 5 pasadas.")

    preview_dir = Path(
        "/home/molano/.gemini/antigravity-cli/brain/07feec6e-b40c-4c7f-9af1-aa8a50b9b26a/scratch/pdf_preview"
    )
    total_pages = verify_bw_and_clean_pdf(preview_dir)
    print(f"[VERIFICADO] PDF: {PDF_OUT.name} | Páginas: {total_pages} | Píxeles: 100% B&N (R=G=B) | Términos prohibidos: 0")


if __name__ == "__main__":
    main()
