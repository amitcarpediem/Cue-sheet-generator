import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AIR Raipur - Cue Sheet Generator", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "segments" not in st.session_state:
    # Pre-loaded sample AIR segments so you can demo immediately
    st.session_state.segments = [
        {
            "Title": "Signature Tune & Vande Mataram",
            "Category": "Opening",
            "Duration_Sec": 180,
            "Remarks": "Studio A Feed",
        },
        {
            "Title": "Pradeshik Samachar (Regional News)",
            "Category": "News",
            "Duration_Sec": 600,
            "Remarks": "RNU Live Relay",
        },
        {
            "Title": "Commercial Spot - Govt Scheme",
            "Category": "Commercial",
            "Duration_Sec": 60,
            "Remarks": "Audio Server Cart 04",
        },
    ]

# --- SIDEBAR: SHIFT METADATA ---
st.sidebar.header("📻 Broadcast Shift Details")
station_name = st.sidebar.text_input("Station", value="All India Radio, Raipur")
channel_name = st.sidebar.selectbox(
    "Channel", ["Primary Channel (MW/FM)", "Vividh Bharati", "FM Rainbow"]
)
broadcast_date = st.sidebar.date_input("Broadcast Date", value=datetime.now())
shift_start_time = st.sidebar.time_input(
    "Shift Start Time", value=datetime.strptime("06:00:00", "%H:%M:%S").time()
)
allocated_mins = st.sidebar.number_input(
    "Allocated Shift Window (Minutes)", min_value=15, max_value=480, value=60
)
duty_officer = st.sidebar.text_input("Duty Officer / Announcer", value="Amit Patel")

# --- MAIN HEADER ---
st.title("🎙️ Automated Cue-Sheet & Transmission Log")
st.markdown(
    f"**Station:** {station_name} | **Channel:** {channel_name} | **Date:** {broadcast_date.strftime('%d-%m-%Y')}"
)
st.divider()

# --- SECTION 1: ADD NEW BROADCAST SEGMENT ---
st.subheader("1. Add Program Segment")
col1, col2, col3, col4, col5 = st.columns([3, 2, 1.5, 2.5, 1])

with col1:
    seg_title = st.text_input("Program / Cue Title", placeholder="e.g., Lok Sangeet")
with col2:
    seg_cat = st.selectbox(
        "Category",
        [
            "Music",
            "News",
            "Announcement",
            "Commercial",
            "Drama/Talk",
            "Opening/Closing",
        ],
    )
with col3:
    seg_dur = st.number_input(
        "Duration (Sec)", min_value=5, max_value=7200, value=300, step=15
    )
with col4:
    seg_rem = st.text_input(
        "Technical Remarks", placeholder="e.g., Console Ch-2 / Live"
    )
with col5:
    st.write("")  # Spacing alignment
    st.write("")
    if st.button("➕ Add", use_container_width=True):
        if seg_title.strip():
            st.session_state.segments.append(
                {
                    "Title": seg_title,
                    "Category": seg_cat,
                    "Duration_Sec": seg_dur,
                    "Remarks": seg_rem if seg_rem else "Normal",
                }
            )
            st.rerun()
        else:
            st.warning("Enter a title.")

# --- SECTION 2: TIME CALCULATION ENGINE ---
current_dt = datetime.combine(broadcast_date, shift_start_time)
calculated_rows = []
total_seconds = 0

for idx, item in enumerate(st.session_state.segments, start=1):
    start_str = current_dt.strftime("%H:%M:%S")
    end_dt = current_dt + timedelta(seconds=item["Duration_Sec"])
    end_str = end_dt.strftime("%H:%M:%S")

    # Format duration as MM:SS
    mins, secs = divmod(item["Duration_Sec"], 60)
    dur_formatted = f"{mins:02d}:{secs:02d}"

    calculated_rows.append(
        {
            "Cue #": idx,
            "Start Time": start_str,
            "End Time": end_str,
            "Duration (MM:SS)": dur_formatted,
            "Program Title": item["Title"],
            "Category": item["Category"],
            "Remarks": item["Remarks"],
        }
    )

    current_dt = end_dt
    total_seconds += item["Duration_Sec"]

df = pd.DataFrame(calculated_rows)

# --- SECTION 3: LIVE SCHEDULE & DRIFT VALIDATION ---
st.subheader("2. Live Master Cue-Sheet")

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Shift Metrics & Overrun Alert
    allocated_seconds = allocated_mins * 60
    diff_seconds = allocated_seconds - total_seconds

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Total Scheduled Airtime", f"{total_seconds // 60}m {total_seconds % 60}s"
    )
    m2.metric("Allocated Shift Window", f"{allocated_mins}m 00s")

    if diff_seconds >= 0:
        m3.metric(
            "Remaining Buffer Time",
            f"{diff_seconds // 60}m {diff_seconds % 60}s",
            delta="On Schedule",
        )
    else:
        overrun = abs(diff_seconds)
        m3.metric(
            "SCHEDULE OVERRUN",
            f"-{overrun // 60}m {overrun % 60}s",
            delta="-Trim Required",
            delta_color="inverse",
        )
        st.error(
            f"⚠️ Broadcast Overrun Alert: Schedule exceeds the {allocated_mins}-minute slot by {overrun // 60} min {overrun % 60} sec!"
        )

    # Delete last item or clear all
    c_del1, c_del2, _ = st.columns([1.5, 1.5, 5])
    if c_del1.button("↩️ Remove Last Cue"):
        st.session_state.segments.pop()
        st.rerun()
    if c_del2.button("🗑️ Clear All"):
        st.session_state.segments = []
        st.rerun()
else:
    st.info("No segments scheduled yet. Add a broadcast cue above.")


# --- SECTION 4: PDF REPORT GENERATOR ---
def generate_pdf(dataframe):
    pdf = FPDF(orientation="L", unit="mm", format="A4")  # Landscape A4 for studio logs
    pdf.add_page()

    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"ALL INDIA RADIO - {station_name.upper()}", ln=True, align="C")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(
        0,
        8,
        f"OFFICIAL BROADCAST CUE-SHEET & TRANSMISSION LOG ({channel_name})",
        ln=True,
        align="C",
    )
    pdf.ln(4)

    # Metadata Bar
    pdf.set_font("Arial", "", 10)
    pdf.cell(90, 8, f"Date: {broadcast_date.strftime('%d-%m-%Y')}", border=1)
    pdf.cell(95, 8, f"Shift Start: {shift_start_time.strftime('%H:%M:%S')}", border=1)
    pdf.cell(92, 8, f"Duty Officer: {duty_officer}", border=1, ln=True)
    pdf.ln(5)

    # Table Header
    pdf.set_font("Arial", "B", 10)
    col_widths = [18, 28, 28, 32, 85, 36, 50]
    headers = [
        "Cue #",
        "Start Time",
        "End Time",
        "Duration",
        "Program Title",
        "Category",
        "Remarks",
    ]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 9, h, border=1, align="C")
    pdf.ln()

    # Table Rows
    pdf.set_font("Arial", "", 9)
    for _, row in dataframe.iterrows():
        pdf.cell(col_widths[0], 8, str(row["Cue #"]), border=1, align="C")
        pdf.cell(col_widths[1], 8, row["Start Time"], border=1, align="C")
        pdf.cell(col_widths[2], 8, row["End Time"], border=1, align="C")
        pdf.cell(col_widths[3], 8, row["Duration (MM:SS)"], border=1, align="C")
        pdf.cell(col_widths[4], 8, f" {row['Program Title'][:42]}", border=1)
        pdf.cell(col_widths[5], 8, row["Category"], border=1, align="C")
        pdf.cell(col_widths[6], 8, f" {row['Remarks'][:25]}", border=1)
        pdf.ln()

    # Footer Signature Block
    pdf.ln(12)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(140, 8, "Signature of Programme Executive: ______________________")
    pdf.cell(
        137,
        8,
        "Signature of Duty Officer (Engineering): ______________________",
        align="R",
    )

    return bytes(pdf.output())


st.divider()
if not df.empty:
    pdf_bytes = generate_pdf(df)
    st.download_button(
        label="📄 Export Official AIR Transmission Log (PDF)",
        data=pdf_bytes,
        file_name=f"AIR_Raipur_CueSheet_{broadcast_date.strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary",
    )
