import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

st.title("AIR Transmission Log Generator")

if "logs" not in st.session_state:
    st.session_state.logs = []

# --- 1. SIDEBAR METADATA ---
with st.sidebar:
    station = st.text_input("Station", "AIR Raipur (101.6 MHz FM)")
    log_date = st.date_input("Date", date.today())
    shift = st.selectbox("Shift", ["Morning", "Afternoon", "Evening"])

# --- 2. ADD PROGRAMME FORM ---
with st.form("log_form", clear_on_submit=True):
    category = st.selectbox(
        "Category",
        ["News Bulletin", "Sponsored Programme", "Commercial Spot", "Music / Filler"],
    )
    title = st.text_input("Programme / Ad ID")
    start_str = st.text_input("Start Time (HH:MM:SS)", "08:00:00")
    end_str = st.text_input("End Time (HH:MM:SS)", "08:05:00")

    if st.form_submit_button("Add Entry"):
        try:
            t1 = datetime.strptime(start_str.strip(), "%H:%M:%S")
            t2 = datetime.strptime(end_str.strip(), "%H:%M:%S")
            mins = round((t2 - t1).total_seconds() / 60, 2)

            if mins > 0:
                st.session_state.logs.append(
                    {
                        "Sr.": len(st.session_state.logs) + 1,
                        "Category": category,
                        "Programme": title or category,
                        "Start": start_str,
                        "End": end_str,
                        "Duration (m)": mins,
                    }
                )
            else:
                st.error("End time must be after Start time.")
        except ValueError:
            st.error("Use HH:MM:SS format.")

# --- 3. DISPLAY TABLE & PDF EXPORT ---
if st.session_state.logs:
    df = pd.DataFrame(st.session_state.logs)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Pandas Metrics
    st.write(f"**Total Airtime:** {round(df['Duration (m)'].sum(), 2)} mins")
    comm_mins = df[df["Category"].str.contains("Commercial|Sponsored")][
        "Duration (m)"
    ].sum()
    st.write(f"**Commercial Airtime:** {round(comm_mins, 2)} mins")

    # PDF Generation
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    table_data = [df.columns.tolist()] + df.values.tolist()
    table = Table(table_data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )

    elements = [
        Paragraph(
            f"<b>{station} — Transmission Log ({log_date} | {shift})</b>",
            styles["Heading2"],
        ),
        Spacer(1, 12),
        table,
    ]
    doc.build(elements)

    st.download_button(
        "Download PDF",
        data=buffer.getvalue(),
        file_name=f"AIR_Log_{log_date}.pdf",
        mime="application/pdf",
    )
