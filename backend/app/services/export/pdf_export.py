from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from app.utils.timeline import PeriodSlot

NAVY = colors.HexColor("#1E293B")
BORDER = colors.HexColor("#CBD5E1")

cell_style = ParagraphStyle(name="Cell", fontSize=7.5, leading=9.5, alignment=1)
header_style = ParagraphStyle(name="Header", fontSize=8, leading=10, textColor=colors.white, alignment=1)
title_style = ParagraphStyle(name="Title", fontSize=15, leading=18, alignment=1, spaceAfter=10)


def build_pdf(
    title: str,
    days: list[str],
    periods_per_day: int,
    period_slots: list[PeriodSlot],
    grid: dict[str, list[str]],
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.0 * cm,
        rightMargin=1.0 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )

    # Header row with period label and clock times
    header_cells = [Paragraph("<b>Day / Period</b>", header_style)]
    for p in range(periods_per_day):
        if p < len(period_slots):
            slot = period_slots[p]
            hdr_text = f"<b>{slot.label}</b><br/>{slot.start_time}–{slot.end_time}"
        else:
            hdr_text = f"<b>P{p + 1}</b>"
        header_cells.append(Paragraph(hdr_text, header_style))

    table_data = [header_cells]
    for day in days:
        row = [Paragraph(f"<b>{escape(day.title())}</b>", header_style)]
        for period in range(periods_per_day):
            text = escape(grid[day][period] or "").replace("\n", "<br/>")
            row.append(Paragraph(text, cell_style))
        table_data.append(row)

    available_width = landscape(A4)[0] - 2.0 * cm
    day_col_width = 2.4 * cm
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
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    doc.build([Paragraph(escape(title), title_style), table])
    return buffer.getvalue()
