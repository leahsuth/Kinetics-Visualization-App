import io
import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF

from src.page_styling.plate_selector import generate_plate_png


def _fit_cell_text(pdf: FPDF, text: str, max_w: float) -> str:
    """Truncate text with ellipsis so it fits inside a table cell."""
    s = str(text)
    if pdf.get_string_width(s) <= max_w:
        return s
    ellipsis = "..."
    if pdf.get_string_width(ellipsis) > max_w:
        return ""
    while s and pdf.get_string_width(s + ellipsis) > max_w:
        s = s[:-1]
    return s + ellipsis


def _draw_table(pdf: FPDF, table_df, *, font_size: int = 9, row_h: float = 6) -> None:
    """Draw a dataframe as a fixed-width table that never exceeds page width."""
    if table_df is None or table_df.empty:
        return

    ncols = max(1, len(table_df.columns))
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin
    col_w = usable_w / ncols
    page_break_y = pdf.page_break_trigger

    def draw_header() -> None:
        pdf.set_font("Helvetica", "B", font_size)
        for col in table_df.columns:
            label = _fit_cell_text(pdf, str(col), col_w - 1.5)
            pdf.cell(col_w, row_h, label, border=1, new_x="RIGHT", new_y="TOP")
        pdf.ln()

    # Avoid orphan header at bottom: ensure space for header + one row.
    if pdf.get_y() + (2 * row_h) > page_break_y:
        pdf.add_page()
    draw_header()

    # Data rows
    pdf.set_font("Helvetica", "", font_size)
    for _, row in table_df.iterrows():
        # Break before row if we are close to bottom.
        if pdf.get_y() + row_h > page_break_y:
            pdf.add_page()
            draw_header()
            pdf.set_font("Helvetica", "", font_size)

        for col in table_df.columns:
            val = row[col]
            cell_str = f"{val:.4f}" if isinstance(val, float) else str(val)
            cell_str = _fit_cell_text(pdf, cell_str, col_w - 1.5)
            pdf.cell(col_w, row_h, cell_str, border=1, new_x="RIGHT", new_y="TOP")
        pdf.ln()


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

    data = df.copy()
    data["time"] = pd.to_numeric(data["time"], errors="coerce")
    data[select_meas] = pd.to_numeric(data[select_meas], errors="coerce")
    data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=["time", select_meas])

    color_col = color_by if color_by in data.columns else (
        "reactant" if "reactant" in data.columns else data.columns[0]
    )

    reaction_col = "reaction" if "reaction" in data.columns else (
        "Reaction" if "Reaction" in data.columns else None
    )
    reactant_col = "reactant" if "reactant" in data.columns else (
        "Analyte" if "Analyte" in data.columns else None
    )

    color_labels = sorted(data[color_col].astype(str).unique().tolist())
    palette = plt.get_cmap("tab10")
    color_map = {
        label: palette(i % 10) for i, label in enumerate(color_labels)
    }

    group_cols = [color_col]
    if reaction_col:
        group_cols.append(reaction_col)
    if reactant_col:
        group_cols.append(reactant_col)

    for keys, group in data.groupby(group_cols, dropna=False):
        group = group.sort_values("time")
        if isinstance(keys, tuple):
            color_label = str(keys[0])
        else:
            color_label = str(keys)
        color = color_map.get(color_label)

        if str(chart_type).lower() == "line":
            ax.plot(group["time"], group[select_meas], marker="o", color=color)
        else:
            ax.scatter(group["time"], group[select_meas], color=color)

    # Legend should reflect the selected color grouping only.
    for label in color_labels:
        ax.plot([], [], marker="o", linestyle="", color=color_map[label], label=label)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label or select_meas)
    ax.set_title(title_text or f"{select_meas} vs. Time", fontsize=14)
    leg = ax.legend(
        title=color_col,
        bbox_to_anchor=(1.01, 1),
        loc="upper left",
        fontsize=10,
        title_fontsize=10,
        frameon=True,
        fancybox=True,
        framealpha=0.95,
        facecolor="white",
        edgecolor="#666666",
        markerscale=1.2,
        handletextpad=0.6,
        borderpad=0.6,
        labelspacing=0.4,
    )
    if leg is not None:
        for t in leg.get_texts():
            t.set_color("#111111")
        leg.get_title().set_color("#111111")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
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


def _heatmap_to_png(pivot: pd.DataFrame) -> bytes:
    """Render a Reaction x Analyte rate heatmap as a matplotlib PNG."""
    data = pivot.to_numpy(dtype=float)
    n_rows, n_cols = data.shape
    fig_w = max(6.5, 0.9 * n_cols + 3)
    fig_h = max(3.5, 0.55 * n_rows + 2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(data, cmap="RdBu_r", aspect="auto")
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels([str(c) for c in pivot.columns], rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels([str(r) for r in pivot.index], fontsize=9)
    for i in range(n_rows):
        for j in range(n_cols):
            val = data[i, j]
            if np.isnan(val):
                continue
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    color="black", fontsize=8)
    ax.set_xlabel("Analyte")
    ax.set_ylabel("Reaction")
    ax.set_title("Initial Rate Heat Map", fontsize=12)
    fig.colorbar(im, ax=ax, label="Rate")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def build_rate_heatmap_png(combined_rate_df: pd.DataFrame) -> bytes | None:
    """Public helper: build a heatmap PNG from the combined rate table."""
    if combined_rate_df is None or combined_rate_df.empty:
        return None
    pivot = combined_rate_df.pivot_table(
        index="Reaction", columns="Analyte", values="Rate", aggfunc="mean"
    )
    if pivot.empty:
        return None
    return _heatmap_to_png(pivot)


def _history_item_to_png(item: dict) -> bytes:
    """Render a single plot-history entry (data + fitted curve) as a matplotlib PNG."""
    single_df = item["single_df"]
    analyte = item["analyte"]
    t_fine = np.array(item["t_fine"])
    y_fit = np.array(item["y_fit"])

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.scatter(single_df["time"], single_df[analyte], label="data", zorder=3)
    ax.plot(t_fine, y_fit, color="#E53935", linewidth=2, label="fitted curve")
    ax.set_xlabel("Time")
    ax.set_ylabel(item.get("selected_measurements", analyte))
    ax.set_title(
        f"Reaction {item['reaction']} - {analyte} ({item['profile_type']})", fontsize=11
    )
    leg = ax.legend(
        fontsize=10,
        frameon=True,
        fancybox=True,
        framealpha=0.95,
        facecolor="white",
        edgecolor="#666666",
        markerscale=1.2,
        handletextpad=0.6,
        borderpad=0.6,
        labelspacing=0.4,
    )
    if leg is not None:
        for t in leg.get_texts():
            t.set_color("#111111")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_report_pdf(
    experiment_setup: dict,
    hplc_file_name: str,
    plot_history: list = None,
    reaction_plots: list = None,
    analyte_ratio_plots: list = None,
    rate_summaries: list = None,
    combined_rate_df: "pd.DataFrame | None" = None,
    heatmap_png: bytes | None = None,
) -> bytes:
    pdf = FPDF()
    # Core PDF fonts only — no external .ttf files so export works in Docker/CI.
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    # ── Header ────────────────────────────────────────────────────────────
    pdf.set_fill_color(0, 122, 115)
    pdf.rect(0, 0, 210, 28, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_y(8)
    pdf.cell(0, 10, "Kinetics Analysis Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, datetime.date.today().isoformat(), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # ── Plate map (from Initial Input plate editor) ───────────────────────
    well_info = experiment_setup.get("well_info") or {}
    if well_info:
        color_by = experiment_setup.get("color_by") or "Reaction"
        reaction_rows = experiment_setup.get("reaction_rows") or []
        n_items = max(1, len(reaction_rows), len(well_info))
        try:
            # Higher DPI + width-only embed keeps the plate sharp (fixed w+h distorts aspect).
            plate_png = generate_plate_png(well_info, color_by, n_items)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, "Reaction Plate Map", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.image(io.BytesIO(plate_png), w=150)
            pdf.ln(6)
            if pdf.get_y() > 240:
                pdf.add_page()
        except Exception as e:
            # Avoid silent failures (e.g. bad image bytes) — show error in PDF instead of empty section.
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, f"(Plate map could not be embedded: {e})")
            pdf.ln(4)

    # ── Individual reaction plots ─────────────────────────────────────────
    if reaction_plots:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Reaction Plots", new_x="LMARGIN", new_y="NEXT")
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
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, f"Reaction {item['reaction']}", new_x="LMARGIN", new_y="NEXT")
                pdf.image(io.BytesIO(rxn_png), w=160)
                pdf.ln(2)
                notes_text = str(item.get("notes") or "").strip()
                if notes_text and notes_text.lower() != "none":
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.multi_cell(0, 5, f"Notes: {notes_text}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                if pdf.get_y() > 250:
                    pdf.add_page()
            except Exception:
                pass

    # ── Analyte ratio plots ───────────────────────────────────────────────
    if analyte_ratio_plots:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Analyte Ratio Plots", new_x="LMARGIN", new_y="NEXT")
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
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, f"Reaction {item['reaction']}", new_x="LMARGIN", new_y="NEXT")
                pdf.image(io.BytesIO(ratio_png), w=160)
                pdf.ln(4)
                if pdf.get_y() > 250:
                    pdf.add_page()
            except Exception:
                pass

    # ── Per-Reaction Rate Summary (one table per reaction) ────────────────
    if rate_summaries:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Rate Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        for entry in rate_summaries:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Reaction {entry['reaction']}", new_x="LMARGIN", new_y="NEXT")
            rt = entry["summary_df"]
            _draw_table(pdf, rt, font_size=9, row_h=6)
            pdf.ln(4)
            if pdf.get_y() > 250:
                pdf.add_page()

    # ── Combined Rate Summary (single table across all reactions) ─────────
    if combined_rate_df is not None and not combined_rate_df.empty:
        # Reorder so Reaction is always first, then preserve remaining columns.
        _cols = ["Reaction"] + [c for c in combined_rate_df.columns if c != "Reaction"]
        rt = combined_rate_df.reindex(columns=_cols)

        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Combined Rate Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        col_w = min(60, 170 / max(len(rt.columns), 1))
        header_h = 7
        row_h = 6
        teal = (0, 122, 115)
        alt_fill = (245, 248, 248)

        def _draw_header() -> None:
            pdf.set_fill_color(*teal)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 9)
            for col in rt.columns:
                pdf.cell(col_w, header_h, str(col), border=0,
                         new_x="RIGHT", new_y="TOP", fill=True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 9)

        _draw_header()
        prev_rxn = None
        group_idx = -1
        for _, row in rt.iterrows():
            if pdf.get_y() > 275:
                pdf.add_page()
                _draw_header()
                prev_rxn = None

            this_rxn = row.get("Reaction")
            if this_rxn != prev_rxn:
                group_idx += 1
                prev_rxn = this_rxn
                show_rxn = True
            else:
                show_rxn = False

            if group_idx % 2 == 1:
                pdf.set_fill_color(*alt_fill)
                fill = True
            else:
                pdf.set_fill_color(255, 255, 255)
                fill = True

            for col in rt.columns:
                val = row[col]
                if col == "Reaction":
                    cell_str = str(val) if show_rxn else ""
                elif isinstance(val, float) and not np.isnan(val):
                    cell_str = f"{val:.4f}"
                elif isinstance(val, float):
                    cell_str = "-"
                elif val is None:
                    cell_str = "-"
                else:
                    cell_str = str(val)
                pdf.cell(col_w, row_h, cell_str, border="B",
                         new_x="RIGHT", new_y="TOP", fill=fill)
            pdf.ln()
        pdf.ln(4)

    # ── Rate heat map (optional) ──────────────────────────────────────────
    if heatmap_png:
        if pdf.get_y() > 180:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Initial Rate Heat Map", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        try:
            pdf.image(io.BytesIO(heatmap_png), w=170)
            pdf.ln(4)
        except Exception:
            pass

    # ── Per-reaction fitted plots + rate tables ───────────────────────────
    if plot_history:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Initial Rate Calculations", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        for item in plot_history:
            rt = item.get("rate_table")
            if rt is None or rt.empty:
                continue

            # Section sub-header
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(
                0, 7,
                f"Reaction {item['reaction']} - {item['analyte']} ({item['profile_type']})",
                new_x="LMARGIN", new_y="NEXT",
            )

            # Fitted curve plot
            if "single_df" in item and "t_fine" in item:
                try:
                    plot_png = _history_item_to_png(item)
                    pdf.image(io.BytesIO(plot_png), w=130)
                    pdf.ln(2)
                except Exception:
                    pass

            # Rate table
            _draw_table(pdf, rt, font_size=9, row_h=6)
            pdf.ln(5)

            # Page break if near bottom
            if pdf.get_y() > 250:
                pdf.add_page()

    return bytes(pdf.output())
