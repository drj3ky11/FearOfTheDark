"""
Tema visual compartido para todas las presentaciones CSBC26.

Paleta de colores, dimensiones y funciones auxiliares para que todos los
bloques compartan el mismo estilo visual sin duplicar constantes.

Uso:
    from _shared.theme import *
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ─── Paleta de colores ────────────────────────────────────────────────────────
C_BG      = RGBColor(0x1A, 0x1A, 0x2E)  # azul marino oscuro — fondo principal
C_BG_SEC  = RGBColor(0x0F, 0x0F, 0x20)  # azul marino profundo — divisores de sección
C_ACCENT  = RGBColor(0xE9, 0x4E, 0x4E)  # rojo — títulos de sección, destacados
C_TITLE   = RGBColor(0xFF, 0xFF, 0xFF)  # blanco — títulos de diapositiva
C_BODY    = RGBColor(0xB8, 0xC0, 0xCC)  # azul-gris — texto de cuerpo
C_MUTED   = RGBColor(0x60, 0x68, 0x78)  # atenuado — etiquetas secundarias
C_CODE_BG = RGBColor(0x0D, 0x1B, 0x2A)  # muy oscuro — cajas de código
C_BADGE   = RGBColor(0x2A, 0x2A, 0x50)  # azul medio — fondo de badges/tags

# ─── Dimensiones de diapositiva (16:9 panorámica) ────────────────────────────
W = Inches(13.33)
H = Inches(7.5)


# ─── Auxiliares de bajo nivel ─────────────────────────────────────────────────

def _set_bg(slide, color: RGBColor) -> None:
    """Rellena el fondo de la diapositiva con un color sólido."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _set_notes(slide, notes: str) -> None:
    """Escribe el guion de oratoria en las notas del orador (modo presentación)."""
    if notes:
        slide.notes_slide.notes_text_frame.text = notes


def _add_rect(slide, x, y, w, h, fill: RGBColor):
    """Agrega un rectángulo relleno sin borde."""
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        x, y, w, h
    )
    shape.line.fill.background()
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    return shape


def _add_txbox(
    slide,
    text: str,
    x, y, w, h,
    size: int = 20,
    color: RGBColor = C_BODY,
    bold: bool = False,
    align=PP_ALIGN.LEFT,
    wrap: bool = True,
) -> None:
    """Agrega un cuadro de texto de un solo párrafo."""
    txb = slide.shapes.add_textbox(x, y, w, h)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = "Calibri"


def _add_multiline(
    slide,
    lines: list[tuple],  # (text, size, color, bold, align)
    x, y, w, h,
) -> None:
    """Agrega un cuadro de texto con múltiples párrafos, cada uno con estilo independiente."""
    txb = slide.shapes.add_textbox(x, y, w, h)
    tf = txb.text_frame
    tf.word_wrap = True

    for i, (text, size, color, bold, align) in enumerate(lines):
        p = tf.paragraphs[i] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.bold = bold
        run.font.name = "Calibri"


def _add_bullets(
    slide,
    title: str,
    bullets: list,
    x=Inches(0.6), y=Inches(1.5),
    w=Inches(12.1), h=Inches(5.5),
    title_y=Inches(0.35),
    title_size=32,
    bullet_size=20,
) -> None:
    """
    Agrega título + lista de viñetas.
    bullets puede contener str (normal) o ("texto", nivel_sangría) para sub-viñetas.
    """
    _add_txbox(slide, title, Inches(0.6), title_y, Inches(12.1), Inches(0.9),
               size=title_size, color=C_TITLE, bold=True)

    txb = slide.shapes.add_textbox(x, y, w, h)
    tf = txb.text_frame
    tf.word_wrap = True

    for i, item in enumerate(bullets):
        if isinstance(item, tuple):
            text, level = item
        else:
            text, level = item, 0

        p = tf.paragraphs[i] if i == 0 else tf.add_paragraph()
        p.level = level
        p.alignment = PP_ALIGN.LEFT

        pPr = p._pPr
        if pPr is None:
            pPr = p._p.get_or_add_pPr()
        indent = Emu(Inches(0.3 * level))
        pPr.set("marL", str(int(indent)))
        pPr.set("indent", str(int(-Inches(0.25))))

        run = p.add_run()
        prefix = "▸  " if level == 0 else "·  "
        run.text = prefix + text
        run.font.size = Pt(bullet_size if level == 0 else bullet_size - 3)
        run.font.color.rgb = C_BODY if level == 0 else C_MUTED
        run.font.name = "Calibri"
        run.font.bold = False


# ─── Constructores de diapositivas ────────────────────────────────────────────

def title_slide(prs: Presentation, title: str, subtitle: str, tag: str, notes: str = "") -> None:
    """Diapositiva de portada con título principal, subtítulo y badge."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, C_BG)

    _add_rect(slide, Inches(0), Inches(0), Inches(0.12), H, C_ACCENT)

    _add_txbox(slide, title,
               Inches(0.6), Inches(2.0), Inches(12.0), Inches(1.8),
               size=44, color=C_TITLE, bold=True)

    _add_txbox(slide, subtitle,
               Inches(0.6), Inches(3.9), Inches(12.0), Inches(1.0),
               size=24, color=C_BODY)

    _add_rect(slide, Inches(0.6), Inches(5.2), Inches(3.6), Inches(0.45), C_BADGE)
    _add_txbox(slide, tag,
               Inches(0.7), Inches(5.22), Inches(3.5), Inches(0.4),
               size=14, color=C_MUTED)

    _add_rect(slide, Inches(0.6), Inches(6.9), Inches(11.5), Inches(0.05), C_ACCENT)
    _set_notes(slide, notes)


def section_slide(prs: Presentation, number: str, title: str, subtitle: str = "", notes: str = "") -> None:
    """Diapositiva divisora de sección con número grande de fondo."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, C_BG_SEC)

    _add_rect(slide, Inches(0), Inches(0), W, Inches(0.1), C_ACCENT)

    _add_txbox(slide, number,
               Inches(9.5), Inches(0.8), Inches(3.5), Inches(5.0),
               size=200, color=RGBColor(0x25, 0x25, 0x45), bold=True, align=PP_ALIGN.RIGHT)

    _add_txbox(slide, "SECCIÓN",
               Inches(0.6), Inches(2.2), Inches(6.0), Inches(0.5),
               size=13, color=C_ACCENT, bold=True)

    _add_txbox(slide, title,
               Inches(0.6), Inches(2.7), Inches(9.0), Inches(1.8),
               size=40, color=C_TITLE, bold=True)

    if subtitle:
        _add_txbox(slide, subtitle,
                   Inches(0.6), Inches(4.6), Inches(9.0), Inches(0.8),
                   size=20, color=C_BODY)
    _set_notes(slide, notes)


def content_slide(
    prs: Presentation,
    title: str,
    bullets: list,
    note: str = "",
    notes: str = "",
) -> None:
    """Diapositiva de contenido con título, lista de viñetas y nota opcional al pie."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, C_BG)
    _add_rect(slide, Inches(0.6), Inches(1.2), Inches(11.5), Inches(0.03), C_ACCENT)
    _add_bullets(slide, title, bullets)
    if note:
        _add_txbox(slide, f"ℹ  {note}",
                   Inches(0.6), Inches(6.85), Inches(12.0), Inches(0.4),
                   size=12, color=C_MUTED)
    _set_notes(slide, notes)


def two_col_slide(
    prs: Presentation,
    title: str,
    left_title: str, left_items: list[str],
    right_title: str, right_items: list[str],
    notes: str = "",
) -> None:
    """Diapositiva de dos columnas con título global y listas independientes."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, C_BG)
    _add_rect(slide, Inches(0.6), Inches(1.2), Inches(11.5), Inches(0.03), C_ACCENT)
    _add_txbox(slide, title, Inches(0.6), Inches(0.35), Inches(12.1), Inches(0.9),
               size=32, color=C_TITLE, bold=True)

    col_w = Inches(5.6)
    col_h = Inches(5.0)

    for col_x, col_title, items in [
        (Inches(0.6),  left_title,  left_items),
        (Inches(7.1), right_title, right_items),
    ]:
        _add_txbox(slide, col_title, col_x, Inches(1.5), col_w, Inches(0.5),
                   size=18, color=C_ACCENT, bold=True)

        txb = slide.shapes.add_textbox(col_x, Inches(2.1), col_w, col_h)
        tf = txb.text_frame
        tf.word_wrap = True
        for i, item in enumerate(items):
            p = tf.paragraphs[i] if i == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = "▸  " + item
            run.font.size = Pt(18)
            run.font.color.rgb = C_BODY
            run.font.name = "Calibri"

    _set_notes(slide, notes)


def table_slide(
    prs: Presentation,
    title: str,
    headers: list[str],
    rows: list[list[str]],
    note: str = "",
    notes: str = "",
) -> None:
    """Diapositiva con tabla de datos, encabezados destacados y filas alternadas."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, C_BG)
    _add_rect(slide, Inches(0.6), Inches(1.2), Inches(11.5), Inches(0.03), C_ACCENT)
    _add_txbox(slide, title, Inches(0.6), Inches(0.35), Inches(12.1), Inches(0.9),
               size=32, color=C_TITLE, bold=True)

    cols = len(headers)
    col_w = Inches(11.5 / cols)
    row_h = Inches(0.48)
    table_top = Inches(1.45)

    _add_rect(slide, Inches(0.6), table_top, Inches(11.5), row_h, C_ACCENT)
    for j, h in enumerate(headers):
        _add_txbox(slide, h,
                   Inches(0.65) + col_w * j, table_top + Emu(60000),
                   col_w - Inches(0.1), row_h,
                   size=14, color=C_TITLE, bold=True)

    for i, row in enumerate(rows):
        row_y = table_top + row_h * (i + 1)
        bg = RGBColor(0x22, 0x22, 0x40) if i % 2 == 0 else RGBColor(0x1E, 0x1E, 0x38)
        _add_rect(slide, Inches(0.6), row_y, Inches(11.5), row_h, bg)
        for j, cell in enumerate(row):
            _add_txbox(slide, cell,
                       Inches(0.65) + col_w * j, row_y + Emu(50000),
                       col_w - Inches(0.1), row_h,
                       size=13, color=C_BODY)

    if note:
        _add_txbox(slide, f"ℹ  {note}",
                   Inches(0.6), Inches(6.85), Inches(12.0), Inches(0.4),
                   size=12, color=C_MUTED)
    _set_notes(slide, notes)


def code_slide(
    prs: Presentation,
    title: str,
    description: str,
    code_lines: list[str],
    note: str = "",
    notes: str = "",
) -> None:
    """Diapositiva con bloque de código monoespacio sobre fondo oscuro."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, C_BG)
    _add_rect(slide, Inches(0.6), Inches(1.2), Inches(11.5), Inches(0.03), C_ACCENT)
    _add_txbox(slide, title, Inches(0.6), Inches(0.35), Inches(12.1), Inches(0.9),
               size=32, color=C_TITLE, bold=True)

    if description:
        _add_txbox(slide, description, Inches(0.6), Inches(1.35), Inches(12.1), Inches(0.6),
                   size=18, color=C_BODY)

    desc_h = Inches(0.7) if description else Inches(0)
    code_top = Inches(1.9) + desc_h
    code_h = Inches(4.8) - desc_h

    _add_rect(slide, Inches(0.5), code_top, Inches(12.3), code_h, C_CODE_BG)

    code_text = "\n".join(code_lines)
    txb = slide.shapes.add_textbox(Inches(0.7), code_top + Inches(0.15),
                                   Inches(12.0), code_h - Inches(0.3))
    tf = txb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = code_text
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0xA8, 0xFF, 0x78)
    run.font.name = "Consolas"

    if note:
        _add_txbox(slide, f"ℹ  {note}",
                   Inches(0.6), Inches(6.85), Inches(12.0), Inches(0.4),
                   size=12, color=C_MUTED)
    _set_notes(slide, notes)


def demo_slide(prs: Presentation, section_title: str, steps: list[str], notebook_path: str = "", notes: str = "") -> None:
    """Diapositiva de demo en vivo con pasos numerados y referencia al notebook."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, C_BG_SEC)
    _add_rect(slide, Inches(0), Inches(0), W, Inches(0.1), C_ACCENT)

    _add_txbox(slide, "DEMO EN VIVO",
               Inches(0.6), Inches(1.0), Inches(12.0), Inches(0.7),
               size=14, color=C_ACCENT, bold=True)
    _add_txbox(slide, section_title,
               Inches(0.6), Inches(1.65), Inches(12.0), Inches(1.2),
               size=36, color=C_TITLE, bold=True)

    if notebook_path:
        _add_txbox(slide, notebook_path,
                   Inches(0.6), Inches(2.9), Inches(8.0), Inches(0.5),
                   size=16, color=C_MUTED)

    txb = slide.shapes.add_textbox(Inches(0.6), Inches(3.6), Inches(12.0), Inches(3.0))
    tf = txb.text_frame
    tf.word_wrap = True
    for i, step in enumerate(steps):
        p = tf.paragraphs[i] if i == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = f"{i+1}.  {step}"
        run.font.size = Pt(19)
        run.font.color.rgb = C_BODY
        run.font.name = "Calibri"

    _set_notes(slide, notes)
