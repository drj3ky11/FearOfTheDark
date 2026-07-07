"""
Tema visual compartido para todas las presentaciones CSBC26.

Construye sobre la plantilla oficial del Cybersecurity Summer Bootcamp 2026
(_shared/plantilla_csbc26.pptx): el fondo de marca, el logo, los patrocinadores
y los layouts ya vienen del máster de PowerPoint. Este módulo solo puebla los
marcadores de posición de cada layout y añade los elementos que la plantilla
no cubre de forma nativa (tablas, bloques de código, dos columnas).

Uso:
    from _shared.theme import *
    prs = new_presentation()
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn

TEMPLATE_PATH = Path(__file__).parent / "plantilla_csbc26.pptx"

# ─── Paleta de colores ────────────────────────────────────────────────────────
# Diapositivas oscuras (portada, sección, cierre) — fondo de marca ya incluido.
C_TITLE  = RGBColor(0xFF, 0xFF, 0xFF)  # blanco — títulos sobre fondo oscuro
C_BODY   = RGBColor(0xD6, 0xDA, 0xE2)  # gris claro — cuerpo sobre fondo oscuro
C_MUTED  = RGBColor(0x9A, 0xA3, 0xB5)  # atenuado sobre fondo oscuro

# Diapositivas claras (contenido, tablas, código) — fondo blanco/gris de marca.
C_TITLE_D = RGBColor(0x1A, 0x1A, 0x2E)  # azul marino — títulos sobre fondo claro
C_BODY_D  = RGBColor(0x33, 0x38, 0x44)  # gris oscuro — cuerpo sobre fondo claro
C_MUTED_D = RGBColor(0x70, 0x78, 0x88)  # atenuado — sobre fondo claro

C_ACCENT  = RGBColor(0xE3, 0x2B, 0x3D)  # rojo de marca — destacados y tablas
C_CODE_BG = RGBColor(0x0D, 0x1B, 0x2A)  # bloque de código, sobre cualquier fondo

# ─── Dimensiones de diapositiva (16:9 panorámica, iguales a la plantilla) ────
W = Inches(13.33)
H = Inches(7.5)

# ─── Layouts de la plantilla usados por este módulo ──────────────────────────
LAYOUT_TITLE   = "Portada presentación"
LAYOUT_SECTION = "Portada sección 1"
LAYOUT_CONTENT = "Bullets"


def new_presentation() -> Presentation:
    """Crea una presentación nueva a partir de la plantilla de marca, sin las diapositivas de ejemplo que trae."""
    prs = Presentation(str(TEMPLATE_PATH))
    xml_slides = prs.slides._sldIdLst
    for sldId in list(xml_slides):
        prs.part.drop_rel(sldId.rId)
        xml_slides.remove(sldId)
    return prs


def _layout(prs: Presentation, name: str):
    """Busca un layout de la plantilla por nombre."""
    for layout in prs.slide_masters[0].slide_layouts:
        if layout.name == name:
            return layout
    raise KeyError(f"Layout {name!r} no encontrado en la plantilla")


def _set_notes(slide, notes: str) -> None:
    """Escribe el guion de oratoria en las notas del orador (modo presentación)."""
    if notes:
        slide.notes_slide.notes_text_frame.text = notes


# ─── Auxiliares de bajo nivel ─────────────────────────────────────────────────

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
    color: RGBColor = C_BODY_D,
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


def _set_title_placeholder(slide, idx: int, text: str, size: int = 24, color: RGBColor = C_TITLE_D) -> None:
    """Escribe el título en el marcador de posición idx de un layout claro."""
    ph = slide.placeholders[idx]
    ph.text_frame.word_wrap = True
    run = ph.text_frame.paragraphs[0].add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = True
    run.font.color.rgb = color
    run.font.name = "Calibri"


def _add_bullets(
    slide,
    ph_idx: int,
    bullets: list,
    size: int = 19,
) -> None:
    """
    Puebla un marcador de posición de cuerpo con una lista de viñetas.
    bullets puede contener str (normal) o ("texto", nivel_sangría) para sub-viñetas.
    """
    tf = slide.placeholders[ph_idx].text_frame
    tf.word_wrap = True

    for i, item in enumerate(bullets):
        if isinstance(item, tuple):
            text, level = item
        else:
            text, level = item, 0

        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = level
        p.alignment = PP_ALIGN.LEFT

        pPr = p._p.get_or_add_pPr()
        indent = Emu(Inches(0.3 * level))
        pPr.set("marL", str(int(indent)))
        pPr.set("indent", str(int(-Inches(0.25))))
        # La plantilla aplica su propia viñeta nativa al marcador de posición;
        # la desactivamos para que solo se vea nuestro prefijo ▸/·.
        pPr.append(pPr.makeelement(qn("a:buNone"), {}))

        run = p.add_run()
        prefix = "▸  " if level == 0 else "·  "
        run.text = prefix + text
        run.font.size = Pt(size if level == 0 else size - 3)
        run.font.color.rgb = C_BODY_D if level == 0 else C_MUTED_D
        run.font.name = "Calibri"
        run.font.bold = False


# ─── Constructores de diapositivas ────────────────────────────────────────────

def title_slide(prs: Presentation, title: str, subtitle: str, tag: str, notes: str = "") -> None:
    """Diapositiva de portada — usa el layout de marca 'Portada presentación'."""
    slide = prs.slides.add_slide(_layout(prs, LAYOUT_TITLE))
    tf = slide.placeholders[10].text_frame
    tf.word_wrap = True

    r = tf.paragraphs[0].add_run()
    r.text = title
    r.font.size = Pt(34)
    r.font.bold = True
    r.font.color.rgb = C_TITLE
    r.font.name = "Calibri"

    p1 = tf.add_paragraph()
    r = p1.add_run()
    r.text = subtitle
    r.font.size = Pt(18)
    r.font.color.rgb = C_BODY
    r.font.name = "Calibri"

    p2 = tf.add_paragraph()
    r = p2.add_run()
    r.text = tag
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = C_MUTED
    r.font.name = "Calibri"

    _set_notes(slide, notes)


def section_slide(prs: Presentation, number: str, title: str, subtitle: str = "", notes: str = "") -> None:
    """Diapositiva divisora de sección — usa el layout de marca 'Portada sección 1'."""
    slide = prs.slides.add_slide(_layout(prs, LAYOUT_SECTION))
    tf = slide.placeholders[10].text_frame
    tf.word_wrap = True

    r = tf.paragraphs[0].add_run()
    r.text = f"SECCIÓN {number}"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = C_ACCENT
    r.font.name = "Calibri"

    p1 = tf.add_paragraph()
    r = p1.add_run()
    r.text = title
    r.font.size = Pt(30)
    r.font.bold = True
    r.font.color.rgb = C_TITLE
    r.font.name = "Calibri"

    if subtitle:
        p2 = tf.add_paragraph()
        r = p2.add_run()
        r.text = subtitle
        r.font.size = Pt(16)
        r.font.color.rgb = C_BODY
        r.font.name = "Calibri"

    _set_notes(slide, notes)


def content_slide(
    prs: Presentation,
    title: str,
    bullets: list,
    note: str = "",
    notes: str = "",
) -> None:
    """Diapositiva de contenido — layout 'Bullets': título + lista de viñetas + nota opcional al pie."""
    slide = prs.slides.add_slide(_layout(prs, LAYOUT_CONTENT))
    _set_title_placeholder(slide, 13, title)
    _add_bullets(slide, 16, bullets)
    if note:
        _add_txbox(slide, f"ℹ  {note}",
                   Inches(1.15), Inches(6.3), Inches(11.0), Inches(0.4),
                   size=11, color=C_MUTED_D)
    _set_notes(slide, notes)


def two_col_slide(
    prs: Presentation,
    title: str,
    left_title: str, left_items: list[str],
    right_title: str, right_items: list[str],
    notes: str = "",
) -> None:
    """Diapositiva de dos columnas — layout 'Bullets' con título global y dos listas independientes."""
    slide = prs.slides.add_slide(_layout(prs, LAYOUT_CONTENT))
    _set_title_placeholder(slide, 13, title)

    col_w = Inches(5.3)
    col_h = Inches(4.2)

    for col_x, col_title, items in [
        (Inches(1.15), left_title,  left_items),
        (Inches(6.8),  right_title, right_items),
    ]:
        _add_txbox(slide, col_title, col_x, Inches(1.85), col_w, Inches(0.45),
                   size=16, color=C_ACCENT, bold=True)

        txb = slide.shapes.add_textbox(col_x, Inches(2.35), col_w, col_h)
        tf = txb.text_frame
        tf.word_wrap = True
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = "▸  " + item
            run.font.size = Pt(16)
            run.font.color.rgb = C_BODY_D
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
    """Diapositiva con tabla de datos — layout 'Bullets' con encabezado destacado y filas alternadas."""
    slide = prs.slides.add_slide(_layout(prs, LAYOUT_CONTENT))
    _set_title_placeholder(slide, 13, title)

    cols = len(headers)
    col_w = Inches(11.0 / cols)
    header_h = Inches(0.4)
    table_top = Inches(1.8)
    font_pt = 11

    # Alto de fila según el contenido: una celda larga necesita más de una
    # línea, y sin este cálculo el texto se desborda visualmente hacia la
    # fila siguiente (LibreOffice ignora word_wrap=False al exportar).
    col_w_in = 11.0 / cols
    chars_per_line = max(8, int((col_w_in - 0.15) / (font_pt * 0.0092)))
    line_h_in = font_pt * 1.25 / 72

    def _lines_needed(text: str) -> int:
        return max(1, -(-len(text) // chars_per_line))  # ceil division

    row_heights = [
        max(0.34, max(_lines_needed(cell) for cell in row) * line_h_in + 0.1)
        for row in rows
    ]

    _add_rect(slide, Inches(1.15), table_top, Inches(11.0), header_h, C_ACCENT)
    for j, h in enumerate(headers):
        _add_txbox(slide, h,
                   Inches(1.2) + col_w * j, table_top + Emu(55000),
                   col_w - Inches(0.1), header_h,
                   size=12, color=C_TITLE, bold=True)

    row_y_in = 1.8 + 0.4
    for i, row in enumerate(rows):
        row_h_in = row_heights[i]
        row_y = Inches(row_y_in)
        bg = RGBColor(0xF1, 0xF2, 0xF6) if i % 2 == 0 else RGBColor(0xFF, 0xFF, 0xFF)
        _add_rect(slide, Inches(1.15), row_y, Inches(11.0), Inches(row_h_in), bg)
        for j, cell in enumerate(row):
            _add_txbox(slide, cell,
                       Inches(1.2) + col_w * j, row_y + Emu(40000),
                       col_w - Inches(0.1), Inches(row_h_in),
                       size=font_pt, color=C_BODY_D)
        row_y_in += row_h_in

    if note:
        _add_txbox(slide, f"ℹ  {note}",
                   Inches(1.15), Inches(max(6.3, row_y_in + 0.15)), Inches(11.0), Inches(0.35),
                   size=10, color=C_MUTED_D)

    _set_notes(slide, notes)


def code_slide(
    prs: Presentation,
    title: str,
    description: str,
    code_lines: list[str],
    note: str = "",
    notes: str = "",
) -> None:
    """Diapositiva con bloque de código monoespacio — layout 'Bullets'."""
    slide = prs.slides.add_slide(_layout(prs, LAYOUT_CONTENT))
    _set_title_placeholder(slide, 13, title)

    y = Inches(1.85)
    if description:
        _add_txbox(slide, description, Inches(1.15), y, Inches(11.0), Inches(0.55),
                   size=16, color=C_BODY_D)
        y = y + Inches(0.6)

    code_h = Inches(6.35) - y

    _add_rect(slide, Inches(1.1), y, Inches(11.1), code_h, C_CODE_BG)

    code_text = "\n".join(code_lines)
    txb = slide.shapes.add_textbox(Inches(1.3), y + Inches(0.15),
                                   Inches(10.7), code_h - Inches(0.3))
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
                   Inches(1.15), Inches(6.3), Inches(11.0), Inches(0.4),
                   size=11, color=C_MUTED_D)

    _set_notes(slide, notes)


def demo_slide(prs: Presentation, section_title: str, steps: list[str], notebook_path: str = "", notes: str = "") -> None:
    """Diapositiva de demo en vivo — reutiliza el layout oscuro 'Portada sección 1' para marcar el contraste."""
    slide = prs.slides.add_slide(_layout(prs, LAYOUT_SECTION))
    tf = slide.placeholders[10].text_frame
    tf.word_wrap = True

    r = tf.paragraphs[0].add_run()
    r.text = "DEMO EN VIVO"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = C_ACCENT
    r.font.name = "Calibri"

    p1 = tf.add_paragraph()
    r = p1.add_run()
    r.text = section_title
    r.font.size = Pt(26)
    r.font.bold = True
    r.font.color.rgb = C_TITLE
    r.font.name = "Calibri"

    if notebook_path:
        p2 = tf.add_paragraph()
        r = p2.add_run()
        r.text = notebook_path
        r.font.size = Pt(14)
        r.font.color.rgb = C_MUTED
        r.font.name = "Calibri"

    txb = slide.shapes.add_textbox(Inches(2.74), Inches(4.0), Inches(7.84), Inches(2.8))
    tf2 = txb.text_frame
    tf2.word_wrap = True
    for i, step in enumerate(steps):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        run = p.add_run()
        run.text = f"{i+1}.  {step}"
        run.font.size = Pt(16)
        run.font.color.rgb = C_BODY
        run.font.name = "Calibri"

    _set_notes(slide, notes)
