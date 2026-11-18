import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- PAGE SETUP ---
st.set_page_config(page_title="AIR Cue-Sheet Generator", layout="wide")
st.title("📻 All India Radio — Automated Cue-Sheet & Log Generator")

# Initialize session state to store log entries during the shift
if "log_entries" not in st.session_state:
    st.session_state.log_entries = []

# --- SIDEBAR: SHIFT DETAILS ---
with st.sidebar:
    st.header("Shift Metadata")
    station_name = st.text_input("Station Name", value="AIR Raipur (101.6 MHz FM)")
    log_date = st.date_input("Broadcast Date", value=date.today())
    shift_name = st.selectbox(
        "Transmission Shift",
        [
            "Morning (05:55 - 10:00)",
            "Afternoon (12:00 - 15:00)",
            "Evening (17:00 - 23:00)",
        ],
    )
    duty_officer = st.text_input(
        "Duty Officer / Transmission Executive", value="VT Trainee"
    )

# --- MAIN AREA: ADD PROGRAMME ENTRY ---
st.subheader("Add Broadcast Entry")
with st.form("entry_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns([2, 3, 1.5, 1.5])

    with col1:
        category = st.selectbox(
            "Category",
            [
                "Signature Tune / Vande Mataram",
                "National News Relay (Delhi)",
                "Regional News Bulletin",
                "Sponsored Programme",
                "Commercial Spot / Ad",
                "PSA (Public Service)",
                "Music / Filler",
            ],
        )
    with col2:
        prog_title = st.text_input(
            "Programme / Tape / Tape ID",
            placeholder="e.g., Samachar Prabhat / Ad-LIC-01",
        )
    with col3:
        scheduled_dur = st.number_input(
            "Scheduled Dur (Mins)", min_value=0.5, max_value=120.0, value=5.0, step=0.5
        )
    with col4:
        remarks = st.text_input("Remarks", value="OK")

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        start_str = st.text_input("Actual Start Time (HH:MM:SS)", value="08:00:00")
    with t_col2:
        end_str = st.text_input("Actual End Time (HH:MM:SS)", value="08:05:00")

    submitted = st.form_submit_button("➕ Add to Transmission Log")

    if submitted:
        try:
            fmt = "%H:%M:%S"
            t_start = datetime.strptime(start_str.strip(), fmt)
            t_end = datetime.strptime(end_str.strip(), fmt)
            actual_sec = (t_end - t_start).total_seconds()

            if actual_sec <= 0:
                st.error("End time must be after Start time!")
            else:
                actual_mins = round(actual_sec / 60, 2)
                diff = round(actual_mins - scheduled_dur, 2)
                status = (
                    "On Time"
                    if abs(diff) <= 0.25
                    else (f"Overrun (+{diff}m)" if diff > 0 else f"Underrun ({diff}m)")
                )

                st.session_state.log_entries.append(
                    {
                        "Sr.": len(st.session_state.log_entries) + 1,
                        "Category": category,
                        "Programme / ID": prog_title if prog_title else category,
                        "Start": start_str,
                        "End": end_str,
                        "Sched (m)": scheduled_dur,
                        "Actual (m)": actual_mins,
                        "Variance": status,
                        "Remarks": remarks,
                    }
                )
                st.success("Entry added to log!")
        except ValueError:
            st.error("Invalid time format! Please use HH:MM:SS (e.g., 08:15:30).")

# --- DISPLAY LIVE LOG TABLE ---
st.divider()
st.subheader("📋 Current Shift Transmission Log")

if st.session_state.log_entries:
    df = pd.DataFrame(st.session_state.log_entries)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Summary Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Items Broadcast", len(df))
    m2.metric("Total Airtime (Mins)", round(df["Actual (m)"].sum(), 2))
    commercial_mins = df[df["Category"].str.contains("Commercial|Sponsored")][
        "Actual (m)"
    ].sum()
    m3.metric("Commercial Airtime (Mins)", round(commercial_mins, 2))

    # --- PDF GENERATION FUNCTION ---
    def generate_pdf(dataframe):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Header
        elements.append(
            Paragraph(
                f"<b>AKASHVANI / ALL INDIA RADIO — TRANSMISSION LOG</b>",
                styles["Title"],
            )
        )
        elements.append(
            Paragraph(
                f"<b>Station:</b> {station_name} | <b>Date:</b> {log_date} | <b>Shift:</b> {shift_name}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(f"<b>Duty Officer:</b> {duty_officer}", styles["Normal"])
        )
        elements.append(Spacer(1, 15))

        # Table Data
        table_data = [dataframe.columns.tolist()] + dataframe.values.tolist()
        t = Table(table_data, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F2F4F8")],
                    ),
                ]
            )
        )
        elements.append(t)
        elements.append(Spacer(1, 30))
        elements.append(
            Paragraph(
                "Signature of Duty Officer: _______________________      Signature of Programme Executive: _______________________",
                styles["Normal"],
            )
        )

        doc.build(elements)
        buffer.seek(0)
        return buffer

    # --- EXPORT BUTTONS ---
    b_col1, b_col2, b_col3 = st.columns([1, 1, 2])
    with b_col1:
        pdf_file = generate_pdf(df)
        st.download_button(
            label="📄 Download Official PDF Log",
            data=pdf_file,
            file_name=f"AIR_Log_{log_date}.pdf",
            mime="application/pdf",
        )
    with b_col2:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📊 Export CSV (Excel)",
            data=csv_data,
            file_name=f"AIR_Log_{log_date}.csv",
            mime="text/csv",
        )
    with b_col3:
        if st.button("🗑️ Clear Current Log"):
            st.session_state.log_entries = []
            st.rerun()
else:
    st.info(
        "No programmes logged yet. Use the form above to add your first broadcast entry."
    )
