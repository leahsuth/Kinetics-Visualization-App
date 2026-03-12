import io
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF


def _df_to_png(df, select_meas: str, color_by: str) -> bytes:
    """Render the kinetics dataframe as a matplotlib PNG — no system browser needed."""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    color_col = color_by if color_by in df.columns else (
        "reactant" if "reactant" in df.columns else df.columns[0]
    )
    for label, group in df.groupby(color_col):
        group = group.sort_values("time")
        ax.plot(group["time"], group[select_meas], marker="o", label=str(label))
    ax.set_xlabel("Time")
    ax.set_ylabel(select_meas)
    ax.set_title(f"{select_meas} vs. time", fontsize=14)
    ax.legend(title=color_col, bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_report_pdf(
    df,
    select_meas: str,
    color_by: str,
    experiment_setup: dict,
    hplc_file_name: str,
    rate_reaction: str,
    rate_value,
    rate_params: dict,
) -> bytes:
    fig_bytes = _df_to_png(df, select_meas, color_by)

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

    # ── Graph ─────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Kinetics Graph", new_x="LMARGIN", new_y="NEXT")
    pdf.image(io.BytesIO(fig_bytes), w=175)
    pdf.ln(4)

    # ── Rate Information ──────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Initial Rate Calculation", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Reaction: {rate_reaction}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Analyte: {rate_params.get('analyte', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Profile type: {rate_params.get('profile_type', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Rate constant (k): {rate_params.get('k', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"C0: {rate_params.get('C0', '-')}    Ce: {rate_params.get('Ce', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    if rate_value is not None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Calculated Rate: {rate_value:.4f}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "Rate not yet calculated.", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
