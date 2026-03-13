import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF
import db

# --- Setup ---
db.init_db()
st.set_page_config(page_title="Anwesenheit", layout="wide")
st.title("Anwesenheitserfassung")

TRAVEL_OPTIONS = ["Keine", "Fahrt", "Übergabefahrt", "Arztbesuch"]


# --- Hilfsfunktionen ---
def generate_time_options():
    options = []
    for h in range(24):
        options.append(f"{h:02d}:00")
        options.append(f"{h:02d}:30")
    options.append("24:00")
    return options


def time_str_to_hours(time_str):
    h, m = map(int, time_str.split(":"))
    return h + m / 60


def generate_pdf(user_name, start_date, end_date, df, total_on_time, total_days, total_hours, percentage, fahrt_count):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Auswertung: {user_name}", ln=True)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Zeitraum: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(4)

    # Tabellenheader
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(30, 8, "Datum", border=1, fill=True)
    pdf.cell(24, 8, "Beginn", border=1, fill=True)
    pdf.cell(24, 8, "Ende", border=1, fill=True)
    pdf.cell(24, 8, "Dauer (h)", border=1, fill=True)
    pdf.cell(50, 8, "Kommentar", border=1, fill=True)
    pdf.cell(38, 8, "Fahrt", border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for _, row in df.iterrows():
        pdf.cell(30, 7, str(row["Datum"]), border=1)
        pdf.cell(24, 7, str(row["Beginn"]), border=1)
        pdf.cell(24, 7, str(row["Ende"]), border=1)
        pdf.cell(24, 7, str(row["Dauer (h)"]), border=1)
        pdf.cell(50, 7, str(row["Kommentar"]) if row["Kommentar"] else "", border=1)
        pdf.cell(38, 7, str(row["Fahrt"]) if row["Fahrt"] else "", border=1)
        pdf.ln()

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Gesamte Anwesenheit: {total_on_time:.1f} h", ln=True)
    pdf.cell(0, 8, f"Tage im Zeitraum: {total_days}", ln=True)
    pdf.cell(0, 8, f"Stunden im Zeitraum: {total_hours} h", ln=True)
    pdf.cell(0, 8, f"Anteil Anwesenheit: {percentage:.1f} %", ln=True)
    pdf.cell(0, 8, f"Anzahl Fahrten: {fahrt_count}", ln=True)

    return bytes(pdf.output())


# --- Sidebar ---
users = db.get_users()
user_names = [u[1] for u in users]
user_dict = {u[1]: u[0] for u in users}

with st.sidebar.expander("Neues Kind erfassen"):
    new_name = st.text_input("Name")
    if st.button("Anlegen"):
        if new_name.strip():
            try:
                db.create_user(new_name.strip())
                st.success(f"'{new_name}' angelegt!")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler: {e}")
        else:
            st.warning("Bitte einen Namen eingeben.")

if user_names:
    selected_user = st.sidebar.selectbox("Wähle Kind", user_names)
    selected_user_id = user_dict[selected_user]
else:
    st.sidebar.warning("Noch kein Kind erfasst.")
    selected_user = None
    selected_user_id = None


# --- Session State Initialisierung ---
time_options = generate_time_options()

if "_entry_date" not in st.session_state:
    st.session_state._entry_date = date.today()
if "_start_idx" not in st.session_state:
    st.session_state._start_idx = 16  # 08:00
if "_end_idx" not in st.session_state:
    st.session_state._end_idx = 32    # 16:00
if "_travel_idx" not in st.session_state:
    st.session_state._travel_idx = 0  # Keine
if "_comment" not in st.session_state:
    st.session_state._comment = ""
if "_last_loaded" not in st.session_state:
    st.session_state._last_loaded = None

# --- Hauptbereich: zwei Spalten ---
left, right = st.columns([1, 2])

# ---- Links: Zeiten erfassen ----
with left:
    st.header("Zeiten erfassen")
    if selected_user_id is None:
        st.warning("Bitte zuerst ein Kind anlegen und auswählen.")
    else:
        entry_date = st.date_input("Datum", value=st.session_state._entry_date)
        st.session_state._entry_date = entry_date

        # Bestehenden Eintrag laden wenn Datum oder Kind wechselt
        load_key = (selected_user_id, entry_date)
        if st.session_state._last_loaded != load_key:
            existing = db.get_entry_for_date(selected_user_id, entry_date)
            if existing:
                st.session_state._start_idx = time_options.index(existing["start_time"])
                st.session_state._end_idx = time_options.index(existing["end_time"])
                existing_travel = existing["travel"] if existing["travel"] in TRAVEL_OPTIONS else "Keine"
                st.session_state._travel_idx = TRAVEL_OPTIONS.index(existing_travel)
                st.session_state._comment = existing["comment"] or ""
            else:
                if not st.session_state.get("_carry_over", False):
                    st.session_state._start_idx = 16
                    st.session_state._end_idx = 32
                st.session_state._travel_idx = 0
                st.session_state._comment = ""
            st.session_state._carry_over = False
            st.session_state._last_loaded = load_key

        existing = db.get_entry_for_date(selected_user_id, entry_date)

        start_time = st.selectbox("Beginn", time_options, index=st.session_state._start_idx)
        st.session_state._start_idx = time_options.index(start_time)

        end_time = st.selectbox("Ende", time_options, index=st.session_state._end_idx)
        st.session_state._end_idx = time_options.index(end_time)

        # Schnellauswahl-Buttons
        g_col, gt_col, aw_col, ew_col = st.columns(4)
        with g_col:
            gemeinsam = st.checkbox("Gemeinsam")
        with gt_col:
            if st.button("Ganzer Tag"):
                st.session_state._start_idx = time_options.index("00:00")
                st.session_state._end_idx = time_options.index("24:00")
                st.rerun()
        with aw_col:
            if st.button("Beginn"):
                st.session_state._start_idx = time_options.index("12:00")
                st.session_state._end_idx = time_options.index("24:00")
                st.rerun()
        with ew_col:
            if st.button("Ende"):
                st.session_state._start_idx = time_options.index("00:00")
                st.session_state._end_idx = time_options.index("12:00")
                st.rerun()

        comment = st.text_input("Kommentar (optional)", key="_comment")
        travel_selection = st.radio("Fahrt", TRAVEL_OPTIONS, index=st.session_state._travel_idx, horizontal=True)
        st.session_state._travel_idx = TRAVEL_OPTIONS.index(travel_selection)

        start_h = time_str_to_hours(start_time)
        end_h = time_str_to_hours(end_time)
        duration = end_h - start_h
        actual_duration = duration / 2 if gemeinsam else duration
        travel_value = None if travel_selection == "Keine" else travel_selection

        dur_col, info_col = st.columns([1, 2])
        with dur_col:
            if duration >= 0:
                st.metric("Dauer", f"{actual_duration:.1f} h")
                if gemeinsam:
                    st.caption(f"(halbiert von {duration:.1f} h)")
        with info_col:
            if existing:
                st.info("Eintrag vorhanden – wird beim Speichern überschrieben.")

        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])
        with btn_col1:
            if st.button("Speichern", type="primary"):
                if duration < 0:
                    st.error("Ende muss nach Beginn liegen!")
                else:
                    db.save_entry(selected_user_id, entry_date, start_time, end_time,
                                  actual_duration, comment, travel_value)
                    st.session_state._last_loaded = None
                    st.success("Gespeichert!")
        with btn_col2:
            if st.button("→ +1 Tag"):
                st.session_state._entry_date += timedelta(days=1)
                st.session_state._carry_over = True
                st.session_state._last_loaded = None
                st.rerun()
        with btn_col3:
            if existing:
                if st.button("Löschen"):
                    db.delete_entry(selected_user_id, entry_date)
                    st.session_state._last_loaded = None
                    st.success("Gelöscht!")
                    st.rerun()


# ---- Rechts: Auswertung ----
with right:
    st.header("Auswertung")
    if selected_user_id is None:
        st.warning("Bitte zuerst ein Kind anlegen und auswählen.")
    else:
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            start_date = st.date_input("Von", value=date.today() - timedelta(days=30), key="auswertung_von")
        with d_col2:
            end_date = st.date_input("Bis", value=date.today(), key="auswertung_bis")

        if st.button("Auswerten"):
            if start_date > end_date:
                st.error("'Von' muss vor 'Bis' liegen.")
            else:
                df = db.get_entries(selected_user_id, start_date, end_date)
                st.session_state._auswertung = {
                    "df": df, "start_date": start_date, "end_date": end_date
                }

        if "_auswertung" in st.session_state and st.session_state._auswertung:
            auswertung = st.session_state._auswertung
            df = auswertung["df"]
            start_date_r = auswertung["start_date"]
            end_date_r = auswertung["end_date"]

            if df.empty:
                st.info("Keine Einträge für diesen Zeitraum.")
            else:
                df_display = df.copy()
                df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d.%m.%Y")
                df_display["duration"] = df_display["duration"].apply(lambda x: f"{float(x):.1f}")
                df_display["comment"] = df_display["comment"].fillna("")
                df_display["travel"] = df_display["travel"].fillna("")
                df_display.columns = ["Datum", "Beginn", "Ende", "Dauer (h)", "Kommentar", "Fahrt"]

                st.caption("Zeile anklicken um Datum links zu öffnen.")
                event = st.dataframe(df_display, use_container_width=True, hide_index=True,
                                     selection_mode="single-row", on_select="rerun")

                if event.selection.rows:
                    selected_idx = event.selection.rows[0]
                    selected_date = pd.to_datetime(df.iloc[selected_idx]["date"]).date()
                    st.session_state._entry_date = selected_date
                    st.session_state._last_loaded = None
                    st.rerun()

                total_days = (end_date_r - start_date_r).days + 1
                total_hours = total_days * 24
                total_on_time = float(df["duration"].astype(float).sum())
                percentage = (total_on_time / total_hours) * 100
                fahrt_count = int(df["travel"].notna().sum() - (df["travel"] == "").sum()
                                  if "travel" in df.columns else 0)

                st.divider()
                c1, c2 = st.columns(2)
                c1.metric("Gesamte Anwesenheit", f"{total_on_time:.1f} h")
                c2.metric("Tage im Zeitraum", total_days)
                c3, c4 = st.columns(2)
                c3.metric("Stunden im Zeitraum", f"{total_hours} h")
                c4.metric("Anteil Anwesenheit", f"{percentage:.1f} %")
                st.metric("Anzahl Fahrten", fahrt_count)

                st.divider()
                pdf_bytes = generate_pdf(
                    selected_user, start_date_r, end_date_r,
                    df_display, total_on_time, total_days, total_hours, percentage, fahrt_count
                )
                st.download_button(
                    label="Als PDF herunterladen",
                    data=pdf_bytes,
                    file_name=f"auswertung_{selected_user}_{start_date_r}_{end_date_r}.pdf",
                    mime="application/pdf"
                )
