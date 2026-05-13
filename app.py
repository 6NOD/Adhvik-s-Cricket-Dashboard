import os
import re
import pandas as pd
import pdfplumber
import streamlit as st
import plotly.express as px

# =====================================================
# CONFIG
# =====================================================

PLAYER_NAME = "Adhvik R"
PDF_FOLDER = "scorecards"

# =====================================================
# STREAMLIT CONFIG
# =====================================================

st.set_page_config(
    page_title="Adhvik Cricket Dashboard",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 Adhvik Cricket Analytics Dashboard")

st.caption("Analyzing CricHeroes PDF scorecards")

# =====================================================
# HELPERS
# =====================================================

def safe_int(value):
    try:
        return int(float(str(value).strip()))
    except:
        return 0


def clean_cell(cell):
    if cell is None:
        return ""
    return str(cell).replace("\n", " ").strip()


# =====================================================
# PARSE BATTING TABLE
# =====================================================

def parse_batting_row(row):

    """
    Expected CricHeroes batting structure:

    Batter | Dismissal | R | B | 4s | 6s | SR

    Example:
    Adhvik R | c X b Y | 45 | 32 | 5 | 2 | 140.62
    """

    cleaned = [clean_cell(c) for c in row]

    row_text = " ".join(cleaned)

    if PLAYER_NAME.lower() not in row_text.lower():
        return None

    numbers = []

    for item in cleaned:

        item = item.strip()

        if re.fullmatch(r"\d+(\.\d+)?", item):
            numbers.append(item)

    # We expect:
    # Runs Balls 4s 6s SR

    if len(numbers) >= 5:

        runs = safe_int(numbers[0])
        balls = safe_int(numbers[1])
        fours = safe_int(numbers[2])
        sixes = safe_int(numbers[3])

        return {
            "Runs": runs,
            "Balls": balls,
            "4s": fours,
            "6s": sixes
        }

    return None


# =====================================================
# PARSE BOWLING TABLE
# =====================================================

def parse_bowling_row(row):

    """
    Expected bowling structure:

    Bowler | O | M | R | W | ECO
    """

    cleaned = [clean_cell(c) for c in row]

    row_text = " ".join(cleaned)

    if PLAYER_NAME.lower() not in row_text.lower():
        return None

    numbers = []

    for item in cleaned:

        item = item.strip()

        if re.fullmatch(r"\d+(\.\d+)?", item):
            numbers.append(item)

    wickets = 0

    # Usually wickets column is 4th numeric value

    if len(numbers) >= 4:
        wickets = safe_int(numbers[3])

    return wickets


# =====================================================
# MAIN PDF EXTRACTION
# =====================================================

def extract_stats_from_pdf(pdf_path):

    batting = {
        "Runs": 0,
        "Balls": 0,
        "4s": 0,
        "6s": 0
    }

    wickets = 0

    try:

        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages:

                tables = page.extract_tables()

                if not tables:
                    continue

                for table in tables:

                    if not table:
                        continue

                    for row in table:

                        if not row:
                            continue

                        row_text = " ".join(
                            [clean_cell(c) for c in row]
                        )

                        # =====================================
                        # BATTING
                        # =====================================

                        if PLAYER_NAME.lower() in row_text.lower():

                            batting_data = parse_batting_row(row)

                            if batting_data:

                                batting = batting_data

                            bowling_data = parse_bowling_row(row)

                            if bowling_data:
                                wickets = max(
                                    wickets,
                                    bowling_data
                                )

        strike_rate = round(
            (batting["Runs"] / batting["Balls"]) * 100,
            2
        ) if batting["Balls"] > 0 else 0

        return {
            "Match PDF": os.path.basename(pdf_path),
            "Runs": batting["Runs"],
            "Balls": batting["Balls"],
            "4s": batting["4s"],
            "6s": batting["6s"],
            "Strike Rate": strike_rate,
            "Wickets": wickets
        }

    except Exception as e:

        st.warning(f"Failed to read: {pdf_path}")

        return None


# =====================================================
# MAIN BUTTON
# =====================================================

if st.button("🚀 Analyze Scorecards"):

    if not os.path.exists(PDF_FOLDER):

        st.error("scorecards folder not found")

    else:

        pdf_files = [

            os.path.join(PDF_FOLDER, file)

            for file in os.listdir(PDF_FOLDER)

            if file.lower().endswith(".pdf")

        ]

        st.success(f"Found {len(pdf_files)} PDF scorecards")

        all_stats = []

        progress = st.progress(0)

        for idx, pdf_file in enumerate(pdf_files):

            progress.progress(
                (idx + 1) / len(pdf_files)
            )

            data = extract_stats_from_pdf(pdf_file)

            if data:
                all_stats.append(data)

        if len(all_stats) == 0:

            st.error("No stats found.")

        else:

            df = pd.DataFrame(all_stats)

            # =============================================
            # SUMMARY METRICS
            # =============================================

            total_matches = len(df)

            total_runs = df["Runs"].sum()

            total_wickets = df["Wickets"].sum()

            highest_score = df["Runs"].max()

            total_4s = df["4s"].sum()

            total_6s = df["6s"].sum()

            avg_sr = round(
                df["Strike Rate"].mean(),
                2
            )

            # =============================================
            # METRIC CARDS
            # =============================================

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Matches", total_matches)

            c2.metric("Runs", total_runs)

            c3.metric("Wickets", total_wickets)

            c4.metric("Highest Score", highest_score)

            c5, c6, c7 = st.columns(3)

            c5.metric("4s", total_4s)

            c6.metric("6s", total_6s)

            c7.metric("Avg Strike Rate", avg_sr)

            st.divider()

            # =============================================
            # MATCH TABLE
            # =============================================

            st.subheader("📋 Match-by-Match Stats")

            st.dataframe(
                df.sort_values(
                    by="Runs",
                    ascending=False
                ),
                use_container_width=True
            )

            # =============================================
            # RUNS CHART
            # =============================================

            st.subheader("📈 Runs Per Match")

            fig_runs = px.bar(
                df,
                x="Match PDF",
                y="Runs"
            )

            st.plotly_chart(
                fig_runs,
                use_container_width=True
            )

            # =============================================
            # WICKETS CHART
            # =============================================

            st.subheader("🎯 Wickets Per Match")

            fig_wickets = px.bar(
                df,
                x="Match PDF",
                y="Wickets"
            )

            st.plotly_chart(
                fig_wickets,
                use_container_width=True
            )

            # =============================================
            # CSV DOWNLOAD
            # =============================================

            csv = df.to_csv(index=False)

            st.download_button(
                "⬇ Download CSV",
                csv,
                file_name="adhvik_stats.csv",
                mime="text/csv"
            )

            st.success("Dashboard generated successfully.")
