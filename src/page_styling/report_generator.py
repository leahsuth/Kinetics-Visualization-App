import io
import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF


# ── Brand palette ─────────────────────────────────────────────────────────
TEAL = (0, 122, 115)          # #007A73
DARK_TEAL = (0, 90, 85)       # #005a55
PALE_TEAL = (246, 251, 250)   # #f6fbfa
BORDER = (215, 222, 221)      # #d7dedd
INK = (31, 38, 38)            # body text
MUTED = (110, 122, 122)       # secondary text

TEAL_HEX = "#007A73"
DARK_TEAL_HEX = "#005a55"
PALE_TEAL_HEX = "#f6fbfa"
BORDER_HEX = "#d7dedd"


def _style_axes(ax) -> None:
    """Apply a light, brand-consistent style to a matplotlib Axes."""
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(BORDER_HEX)
    ax.tick_params(colors="#1f2626", labelsize=9)
    ax.grid(True, linestyle="--", alpha=0.35, color=BORDER_HEX)
    ax.set_axisbelow(True)


PLOTLY_QUALITATIVE = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
]


def _df_to_png(
    df,
    select_meas: str,
    color_by: str,
    chart_type: str = "Scatter",
    title_text: str | None = None,
    x_label: str = "Time",
    y_label: str | None = None,
) -> bytes:
    """Render the kinetics dataframe as a matplotlib PNG."""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    color_col = color_by if color_by in df.columns else (
        "reactant" if "reactant" in df.columns else df.columns[0]
    )
    # Iterate groups in first-seen order so the color assignment matches the
    # browser's Plotly figure (color_discrete_sequence + categorical color).
    groups = list(df.groupby(color_col, sort=False))
    is_line = str(chart_type or "").strip().lower() == "line"
    for i, (label, group) in enumerate(groups):
        group = group.copy()
        group["time"] = pd.to_numeric(group["time"], errors="coerce")
        group[select_meas] = pd.to_numeric(group[select_meas], errors="coerce")
        group = group.dropna(subset=["time", select_meas]).sort_values("time")
        if group.empty:
            continue
        color = PLOTLY_QUALITATIVE[i % len(PLOTLY_QUALITATIVE)]
        if is_line:
            ax.plot(
                group["time"], group[select_meas], label=str(label),
                color=color, marker="o", markersize=4, linewidth=1.8, zorder=3,
            )
        else:
            ax.scatter(
                group["time"], group[select_meas], label=str(label),
                color=color, s=28, edgecolor="white", linewidth=0.6, zorder=3,
            )
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label or select_meas)
    ax.set_title(title_text or f"{select_meas} vs. Time", fontsize=13, color=DARK_TEAL_HEX, pad=10)
    leg = ax.legend(title=color_col, bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8, frameon=False)
    if leg and leg.get_title():
        leg.get_title().set_color(DARK_TEAL_HEX)
    _style_axes(ax)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def analyte_ratio_to_png(
    df,
    color_by: str,
    title_text: str,
    x_label: str,
    y_label: str,
    chart_type: str = "Scatter",
) -> bytes:
    """Render the analyte ratio dataframe as a matplotlib PNG."""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    color_col = color_by if color_by in df.columns else (
        "reactant" if "reactant" in df.columns else df.columns[0]
    )
    is_line = str(chart_type or "").strip().lower() == "line"
    for label, group in df.groupby(color_col):
        group = group.sort_values("time")
        if is_line:
            ax.plot(group["time"], group["analyte_ratio"], marker="o", label=str(label))
        else:
            ax.scatter(group["time"], group["analyte_ratio"], label=str(label))
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title_text or "Analyte Ratio vs. Time", fontsize=14)
    ax.legend(title=color_col, bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _heatmap_to_png(pivot: pd.DataFrame,
                    figsize: tuple[float, float] | None = None) -> bytes:
    """Render a Reaction x Analyte rate heatmap as a matplotlib PNG.

    Always uses a diverging blue→white→red scale centered at 0, with the
    color range clipped to a robust 95th-percentile of |rate| so a single
    extreme value can't wash out smaller but meaningful differences.
    """
    from matplotlib.colors import TwoSlopeNorm

    data = pivot.to_numpy(dtype=float)
    n_rows, n_cols = data.shape

    if figsize is not None:
        fig_w, fig_h = figsize
    else:
        # Aspect tuned to the PDF embed box (180×230 mm ≈ 0.78). Keep cells from
        # collapsing when there are many reactions.
        fig_w = max(8.0, 1.05 * n_cols + 3.0)
        fig_h = max(5.0, 0.65 * n_rows + 2.4)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    finite = data[np.isfinite(data)]
    if finite.size > 0:
        abs_max = float(np.nanpercentile(np.abs(finite), 95)) or float(np.max(np.abs(finite))) or 1.0
    else:
        abs_max = 1.0
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-abs_max, vmax=abs_max)

    cmap = plt.get_cmap("RdBu_r").copy()
    cmap.set_bad("#eef1f1")
    masked = np.ma.masked_invalid(data)
    im = ax.imshow(masked, cmap=cmap, norm=norm, aspect="auto",
                   interpolation="nearest")

    # Subtle white gridlines between cells for separation.
    ax.set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.0)
    ax.tick_params(which="minor", length=0)

    ax.set_xticks(range(n_cols))
    ax.set_xticklabels([str(c) for c in pivot.columns],
                       rotation=45, ha="right", fontsize=11)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels([str(r) for r in pivot.index], fontsize=11)
    ax.tick_params(axis="both", colors="#1f2626", length=3, color=BORDER_HEX)

    # Subtle, small annotations - only when there's room.
    if n_rows <= 28 and n_cols <= 14:
        cell_fs = 7 if (n_rows <= 18 and n_cols <= 10) else 6
        for i in range(n_rows):
            for j in range(n_cols):
                val = data[i, j]
                if not np.isfinite(val):
                    continue
                rgba = im.cmap(im.norm(val))
                luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                txt_color = "white" if luminance < 0.45 else "#1f2626"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        color=txt_color, fontsize=cell_fs, alpha=0.85)

    ax.set_xlabel("Analyte / Condition", fontsize=13, color=DARK_TEAL_HEX,
                  labelpad=10, fontweight="bold")
    ax.set_ylabel("Reaction ID", fontsize=13, color=DARK_TEAL_HEX,
                  labelpad=10, fontweight="bold")
    ax.set_title("Initial Rate Heat Map", fontsize=15, color=DARK_TEAL_HEX,
                 pad=12, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_visible(False)

    cbar = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.04, aspect=28)
    cbar.set_label("Initial Rate", fontsize=12, color=DARK_TEAL_HEX,
                   fontweight="bold", labelpad=8)
    cbar.ax.tick_params(labelsize=10, colors="#1f2626")
    cbar.outline.set_visible(False)

    fig.tight_layout(pad=0.6)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, facecolor="white",
                bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def build_rate_heatmap_png(combined_rate_df: pd.DataFrame,
                           figsize: tuple[float, float] | None = None) -> bytes | None:
    """Public helper: build a heatmap PNG from the combined rate table."""
    if combined_rate_df is None or combined_rate_df.empty:
        return None
    pivot = combined_rate_df.pivot_table(
        index="Reaction", columns="Analyte", values="Rate", aggfunc="mean"
    )
    if pivot.empty:
        return None
    return _heatmap_to_png(pivot, figsize=figsize)


def _history_item_to_png(item: dict) -> bytes:
    """Render a single plot-history entry (data + fitted curve) as a matplotlib PNG."""
    single_df = item["single_df"]
    analyte = item["analyte"]
    t_fine = np.array(item["t_fine"])
    y_fit = np.array(item["y_fit"])

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.scatter(
        single_df["time"], single_df[analyte],
        label="data", color=TEAL_HEX, s=32, edgecolor="white", linewidth=0.7, zorder=3,
    )
    ax.plot(t_fine, y_fit, color=DARK_TEAL_HEX, linewidth=2.0, label="fitted curve", zorder=2)
    ax.set_xlabel("Time")
    ax.set_ylabel(item.get("selected_measurements", analyte))
    ax.set_title(
        f"Reaction {item['reaction']} - {analyte} ({item['profile_type']})",
        fontsize=11, color=DARK_TEAL_HEX, pad=8,
    )
    ax.legend(fontsize=8, frameon=False, loc="best")
    _style_axes(ax)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# ── Branded PDF subclass ──────────────────────────────────────────────────
class _BrandedPDF(FPDF):
    """FPDF subclass that paints a brand header strip and footer on every page."""

    def __init__(self, file_name: str = "-"):
        super().__init__()
        self.file_name = file_name
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(15, 22, 15)

    def header(self) -> None:
        # Thin teal accent bar across the top of every page.
        self.set_fill_color(*TEAL)
        self.rect(0, 0, self.w, 6, style="F")
        self.set_fill_color(*PALE_TEAL)
        self.rect(0, 6, self.w, 1, style="F")
        self.set_y(10)
        self.set_text_color(*DARK_TEAL)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 5, "Kinetics Analysis Report", align="L")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 5, datetime.date.today().isoformat(), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*INK)
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_y(-11)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 5, str(self.file_name), align="L")
        self.cell(0, 5, f"Page {self.page_no()} / {{nb}}", align="R")
        self.set_text_color(*INK)


# ── Layout helpers ────────────────────────────────────────────────────────
def _section_title(pdf: FPDF, text: str) -> None:
    """Major section heading with a teal underline."""
    if pdf.get_y() > pdf.h - pdf.b_margin - 30:
        pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*DARK_TEAL)
    pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y()
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.8)
    pdf.line(pdf.l_margin, y, pdf.l_margin + 28, y)
    pdf.set_draw_color(*BORDER)
    pdf.set_line_width(0.2)
    pdf.line(pdf.l_margin + 28, y, pdf.w - pdf.r_margin, y)
    pdf.set_text_color(*INK)
    pdf.ln(4)


def _subsection_title(pdf: FPDF, text: str) -> None:
    """Smaller heading used for sub-blocks within a section."""
    if pdf.get_y() > pdf.h - pdf.b_margin - 22:
        pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*DARK_TEAL)
    pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)
    pdf.ln(1)


def _key_value_block(pdf: FPDF, items: list[tuple[str, str]]) -> None:
    """Render an aligned label/value block (e.g. methods metadata)."""
    pdf.set_font("Helvetica", "", 10)
    label_w = 42
    value_w = pdf.w - pdf.l_margin - pdf.r_margin - label_w
    line_h = 5.5
    for label, value in items:
        if pdf.get_y() > pdf.h - pdf.b_margin - line_h * 2:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK_TEAL)
        pdf.cell(label_w, line_h, label, new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*INK)
        pdf.multi_cell(value_w, line_h, str(value) if value not in (None, "") else "-",
                       new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _draw_table(pdf: FPDF, columns: list[str], rows: list[list[str]],
                col_widths: list[float] | None = None,
                group_col_index: int | None = None) -> None:
    """Draw a styled data table.

    If group_col_index is provided, rows are visually grouped by that column
    (alternating subtle teal tint per group, value shown only on first row).
    """
    if not columns:
        return
    avail = pdf.w - pdf.l_margin - pdf.r_margin
    if col_widths is None:
        col_widths = [avail / len(columns)] * len(columns)
    header_h = 7.5
    row_h = 6.0

    def draw_header():
        pdf.set_fill_color(*TEAL)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        for c, w in zip(columns, col_widths):
            pdf.cell(w, header_h, str(c), border=0, align="L",
                     new_x="RIGHT", new_y="TOP", fill=True)
        pdf.ln()
        pdf.set_text_color(*INK)

    draw_header()

    prev_group = object()
    group_idx = -1
    for row in rows:
        if pdf.get_y() > pdf.h - pdf.b_margin - row_h:
            pdf.add_page()
            draw_header()
            prev_group = object()

        if group_col_index is not None:
            this_group = row[group_col_index]
            if this_group != prev_group:
                group_idx += 1
                prev_group = this_group
                show_group = True
            else:
                show_group = False
        else:
            group_idx += 1
            show_group = True

        if group_idx % 2 == 1:
            pdf.set_fill_color(*PALE_TEAL)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(*BORDER)
        pdf.set_line_width(0.15)
        pdf.set_font("Helvetica", "", 9)

        for i, (val, w) in enumerate(zip(row, col_widths)):
            if group_col_index is not None and i == group_col_index and not show_group:
                cell_str = ""
            else:
                cell_str = "" if val is None else str(val)
            pdf.cell(w, row_h, cell_str, border="B", align="L",
                     new_x="RIGHT", new_y="TOP", fill=True)
        pdf.ln()
    pdf.ln(3)


def _format_value(val) -> str:
    if val is None:
        return "-"
    if isinstance(val, float):
        if np.isnan(val):
            return "-"
        return f"{val:.4f}"
    s = str(val).strip()
    return s if s else "-"


# ── Cover banner ──────────────────────────────────────────────────────────
def _draw_cover_banner(pdf: FPDF, file_name: str) -> None:
    """Large teal hero block at the top of the first page."""
    banner_h = 36
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, pdf.w, banner_h, style="F")
    pdf.set_fill_color(*DARK_TEAL)
    pdf.rect(0, banner_h, pdf.w, 2, style="F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_y(11)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 10, "Kinetics Analysis Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, f"Source: {file_name}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, datetime.date.today().strftime("%B %d, %Y"),
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*INK)
    pdf.set_y(banner_h + 8)


# ── Public API ────────────────────────────────────────────────────────────
def generate_report_pdf(
    experiment_setup: dict,
    hplc_file_name: str,
    plot_history: list = None,
    reaction_plots: list = None,
    analyte_ratio_plots: list = None,
    rate_summaries: list = None,
    combined_rate_df: "pd.DataFrame | None" = None,
    heatmap_png: bytes | None = None,
    plate_map_png: bytes | None = None,
) -> bytes:
    experiment_setup = experiment_setup or {}
    pdf = _BrandedPDF(file_name=hplc_file_name or "-")
    pdf.alias_nb_pages()
    pdf.add_page()

    # The page_no() == 1 header is overpainted by the cover banner.
    _draw_cover_banner(pdf, hplc_file_name or "-")

    # ── 1. Experimental Setup ─────────────────────────────────────────────
    _section_title(pdf, "1.  Experimental Setup")

    source = str(experiment_setup.get("source", "-")).strip() or "-"
    timepoints = experiment_setup.get("timepoints") or []
    cond_cols = experiment_setup.get("condition_columns") or []
    reaction_rows = experiment_setup.get("reaction_rows") or []
    reactions_list = experiment_setup.get("reactions") or []
    color_by = experiment_setup.get("color_by") or "-"

    n_reactions = len(reactions_list) if reactions_list else (
        len(reaction_rows) if isinstance(reaction_rows, list) else 0
    )
    timepoints_str = ", ".join(str(t) for t in timepoints) if timepoints else "-"
    if len(timepoints_str) > 220:
        timepoints_str = timepoints_str[:217] + "..."

    _key_value_block(pdf, [
        ("Data source", source.capitalize() if source != "-" else "-"),
        ("Source file", hplc_file_name or "-"),
        ("Reactions", str(n_reactions) if n_reactions else "-"),
        ("Timepoints", timepoints_str),
        ("Condition columns", ", ".join(cond_cols) if cond_cols else "-"),
        ("Color grouping", str(color_by)),
    ])

    # Reaction conditions table (only when it adds information).
    if isinstance(reaction_rows, list) and reaction_rows and isinstance(reaction_rows[0], dict):
        _subsection_title(pdf, "Reaction conditions")
        keep = ["Reaction", "Reaction_Well"] + list(cond_cols) + ["Notes"]
        keep = [k for k in keep if any(k in r for r in reaction_rows)]
        if keep:
            avail = pdf.w - pdf.l_margin - pdf.r_margin
            base = avail / len(keep)
            col_widths = [min(max(base, 18), 70) for _ in keep]
            scale = avail / sum(col_widths)
            col_widths = [w * scale for w in col_widths]
            rows_out = []
            for r in reaction_rows:
                rows_out.append([_format_value(r.get(k)) for k in keep])
            display_cols = [c.replace("_", " ") for c in keep]
            _draw_table(pdf, display_cols, rows_out, col_widths=col_widths)

    # Plate map image (when generated on the setup page).
    if plate_map_png:
        if pdf.get_y() > pdf.h - pdf.b_margin - 90:
            pdf.add_page()
        _subsection_title(pdf, "Plate map")
        try:
            pdf.image(io.BytesIO(plate_map_png), w=170, keep_aspect_ratio=True)
            pdf.ln(3)
        except Exception as _e:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(0, 5, f"Plate map could not be embedded: {_e}",
                           new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*INK)
            pdf.ln(3)

        # Per-reaction notes from the plate editor, listed beneath the plate.
        well_info = experiment_setup.get("well_info") or {}
        plate_notes: list[tuple[str, str, str]] = []  # (reaction, well, note)
        _seen_notes: set = set()
        for well_id, info in well_info.items():
            note = str(info.get("Notes", "") or "").strip()
            if not note or note.lower() == "none":
                continue
            rxn = str(info.get("Reaction", "")).strip() or "-"
            entry = (rxn, str(well_id), note)
            if entry in _seen_notes:
                continue
            _seen_notes.add(entry)
            plate_notes.append(entry)
        if plate_notes:
            plate_notes.sort(key=lambda e: (e[0], e[1]))
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*DARK_TEAL)
            pdf.cell(0, 6, "Plate notes", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*INK)
            pdf.set_font("Helvetica", "", 9)
            for rxn, well, note in plate_notes:
                pdf.multi_cell(0, 5,
                               f"  - Reaction {rxn} ({well}): {note}",
                               new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # ── 2. Reaction Plots (raw data) ──────────────────────────────────────
    if reaction_plots:
        _section_title(pdf, "2.  Reaction Plots")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 5,
                       "Raw measurement traces per reaction, grouped by analyte / reactant.",
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.ln(2)

        for item in reaction_plots:
            try:
                rxn_png = _df_to_png(
                    item["df"],
                    item["select_meas"],
                    item["color_by"],
                    chart_type=item.get("chart_type", "Scatter"),
                    title_text=item.get("title_text"),
                    x_label=item.get("x_label", "Time"),
                    y_label=item.get("y_label"),
                )
                if pdf.get_y() > pdf.h - pdf.b_margin - 90:
                    pdf.add_page()
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*DARK_TEAL)
                pdf.cell(0, 6, f"Reaction {item['reaction']}",
                         new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(*INK)
                pdf.image(io.BytesIO(rxn_png), w=170)
                pdf.ln(1)
                notes_text = str(item.get("notes") or "").strip()
                if notes_text and notes_text.lower() != "none":
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.set_text_color(*MUTED)
                    pdf.multi_cell(0, 5, f"Notes: {notes_text}",
                                   new_x="LMARGIN", new_y="NEXT")
                    pdf.set_text_color(*INK)
                pdf.ln(3)
            except Exception:
                pass

    # ── 3. Analyte Ratio Plots ───────────────────────────────────────────
    if analyte_ratio_plots:
        _section_title(pdf, "3.  Analyte Ratio Plots")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 5,
                       "Analyte ratio traces (numerator / denominator) per reaction.",
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.ln(2)
        for item in analyte_ratio_plots:
            try:
                ratio_png = analyte_ratio_to_png(
                    item["df"],
                    item.get("color_by", item.get("reaction_col", "reaction")),
                    chart_type=item.get("chart_type", "Scatter"),
                    title_text=item.get("title_text"),
                    x_label=item.get("x_label", "Time"),
                    y_label=item.get("y_label", "Analyte Ratio"),
                )
                if pdf.get_y() > pdf.h - pdf.b_margin - 90:
                    pdf.add_page()
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*DARK_TEAL)
                pdf.cell(0, 6, f"Reaction {item['reaction']}",
                         new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(*INK)
                pdf.image(io.BytesIO(ratio_png), w=170)
                pdf.ln(3)
            except Exception:
                pass

    # ── 4. Rate Summary ───────────────────────────────────────────────────
    if combined_rate_df is not None and not combined_rate_df.empty:
        _section_title(pdf, "4.  Rate Summary")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 5,
                       "Initial rates across all selected reactions and analytes.",
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.ln(1)

        cols_in = ["Reaction"] + [c for c in combined_rate_df.columns if c != "Reaction"]
        rt = combined_rate_df.reindex(columns=cols_in)
        avail = pdf.w - pdf.l_margin - pdf.r_margin
        col_widths = [avail / len(rt.columns)] * len(rt.columns)
        rows_out = [[_format_value(v) for v in row] for _, row in rt.iterrows()]
        _draw_table(
            pdf,
            list(rt.columns),
            rows_out,
            col_widths=col_widths,
            group_col_index=0,
        )

    # ── 5. Initial Rate Heat Map ─────────────────────────────────────────
    if heatmap_png:
        pdf.add_page()
        _section_title(pdf, "5.  Initial Rate Heat Map")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 5,
                       "Reaction x analyte view of initial rates. Sequential colormap "
                       "for same-sign rates; diverging colormap centered at zero when "
                       "rates change sign.",
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.ln(2)
        try:
            # Full page width; height auto-derives from the PNG aspect (the
            # heatmap is generated with a wide/short aspect that matches what
            # the user sees in the browser).
            pdf.image(io.BytesIO(heatmap_png), w=180)
        except Exception as _e:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(0, 5, f"Heat map could not be embedded: {_e}",
                           new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*INK)

    # ── 5. Initial Rate Calculations (per-reaction fits) ─────────────────
    if plot_history:
        pdf.add_page()
        _section_title(pdf, "6.  Initial Rate Calculations")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 5,
                       "Per-reaction fitted curves and the parameters used to extract "
                       "initial rates.",
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.ln(2)

        for item in plot_history:
            rt = item.get("rate_table")
            if rt is None or rt.empty:
                continue

            if pdf.get_y() > pdf.h - pdf.b_margin - 80:
                pdf.add_page()

            _subsection_title(
                pdf,
                f"Reaction {item['reaction']} - {item['analyte']} ({item['profile_type']})",
            )

            if "single_df" in item and "t_fine" in item:
                try:
                    plot_png = _history_item_to_png(item)
                    pdf.image(io.BytesIO(plot_png), w=140)
                    pdf.ln(2)
                except Exception:
                    pass

            avail = pdf.w - pdf.l_margin - pdf.r_margin
            col_widths = [avail / len(rt.columns)] * len(rt.columns)
            rows_out = [[_format_value(v) for v in row] for _, row in rt.iterrows()]
            _draw_table(pdf, list(rt.columns), rows_out, col_widths=col_widths)

            pdf.ln(2)

    return bytes(pdf.output())
