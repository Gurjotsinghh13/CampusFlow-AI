from io import BytesIO
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

NAVY = colors.HexColor("#1E293B")
BORDER = colors.HexColor("#CBD5E1")

cell_style = ParagraphStyle(name="Cell", fontSize=8, leading=10, alignment=1)
header_style = ParagraphStyle(name="Header", fontSize=9, leading=11, textColor=colors.white, alignment=1)
title_style = ParagraphStyle(name="Title", fontSize=16, leading=20, alignment=1, spaceAfter=12)


def build_pdf(title: str, days: list[str], periods_per_day: int, grid: dict[str, list[str]]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    header_row = [Paragraph("Day / Period", header_style)] + [
        Paragraph(f"P{p + 1}", header_style) for p in range(periods_per_day)
    ]
    table_data = [header_row]
    for day in days:
        row = [Paragraph(escape(day.title()), header_style)]
        for period in range(periods_per_day):
            text = escape(grid[day][period] or "").replace("\n", "<br/>")
            row.append(Paragraph(text, cell_style))
        table_data.append(row)

    available_width = landscape(A4)[0] - 2.4 * cm
    day_col_width = 2.6 * cm
    period_col_width = (available_width - day_col_width) / max(periods_per_day, 1)
    col_widths = [day_col_width] + [period_col_width] * periods_per_day

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("BACKGROUND", (0, 1), (0, -1), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    doc.build([Paragraph(escape(title), title_style), table])
    return buffer.getvalue()
