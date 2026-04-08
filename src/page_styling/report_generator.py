import io
import datetime
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF


def _df_to_png(
    df,
    select_meas: str,
    color_by: str,
    title_text: str | None = None,
    x_label: str = "Time",
    y_label: str | None = None,
) -> bytes:
    """Render the kinetics dataframe as a matplotlib PNG."""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    color_col = color_by if color_by in df.columns else (
        "reactant" if "reactant" in df.columns else df.columns[0]
    )
    for label, group in df.groupby(color_col):
        group = group.sort_values("time")
        ax.scatter(group["time"], group[select_meas], label=str(label))
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label or select_meas)
    ax.set_title(title_text or f"{select_meas} vs. Time", fontsize=14)
    ax.legend(title=color_col, bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


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
    ax.legend(fontsize=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_report_pdf(
    experiment_setup: dict,
    hplc_file_name: str,
    plot_history: list = None,
    reaction_plots: list = None,
    rate_summaries: list = None,
) -> bytes:
    pdf = FPDF()
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
                    title_text=item.get("title_text"),
                    x_label=item.get("x_label", "Time"),
                    y_label=item.get("y_label"),
                )
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, f"Reaction {item['reaction']}", new_x="LMARGIN", new_y="NEXT")
                pdf.image(io.BytesIO(rxn_png), w=160)
                pdf.ln(4)
                if pdf.get_y() > 250:
                    pdf.add_page()
            except Exception:
                pass

    # ── Rate Summary (Controls table per reaction) ────────────────────────
    if rate_summaries:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Rate Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        col_w = 45
        for entry in rate_summaries:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Reaction {entry['reaction']}", new_x="LMARGIN", new_y="NEXT")
            rt = entry["summary_df"]
            pdf.set_font("Helvetica", "B", 9)
            for col in rt.columns:
                pdf.cell(col_w, 6, str(col), border=1, new_x="RIGHT", new_y="TOP")
            pdf.ln()
            pdf.set_font("Helvetica", "", 9)
            for _, row in rt.iterrows():
                for col in rt.columns:
                    val = row[col]
                    cell_str = f"{val:.4f}" if isinstance(val, float) else str(val)
                    pdf.cell(col_w, 6, cell_str, border=1, new_x="RIGHT", new_y="TOP")
                pdf.ln()
            pdf.ln(4)
            if pdf.get_y() > 250:
                pdf.add_page()

    # ── Per-reaction fitted plots + rate tables ───────────────────────────
    if plot_history:
        pdf.set_font("Helvetica", "B", 13)
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
            pdf.set_font("Helvetica", "B", 9)
            col_w = 30
            for col in rt.columns:
                pdf.cell(col_w, 6, str(col), border=1, new_x="RIGHT", new_y="TOP")
            pdf.ln()
            pdf.set_font("Helvetica", "", 9)
            for _, row in rt.iterrows():
                for col in rt.columns:
                    val = row[col]
                    cell_str = f"{val:.4f}" if isinstance(val, float) else str(val)
                    pdf.cell(col_w, 6, cell_str, border=1, new_x="RIGHT", new_y="TOP")
                pdf.ln()
            pdf.ln(5)

            # Page break if near bottom
            if pdf.get_y() > 250:
                pdf.add_page()

    return bytes(pdf.output())
