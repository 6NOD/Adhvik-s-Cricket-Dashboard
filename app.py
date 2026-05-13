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

# =====================================================
# HELPERS
# =====================================================


def safe_int(value):
    try:
        return int(value)
    except:
        return 0


# =====================================================
# PDF PARSER
# =====================================================


def extract_stats_from_pdf(pdf_path):

    try:

        full_text = ""

        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages:

                text = page.extract_text()

                if text:
                    full_text += "\n" + text

        if PLAYER_NAME.lower() not in full_text.lower():
            return None

        # =================================================
        # RUNS + BALLS
        # Example:
        # Adhvik 45 (32)
        # =================================================

        batting_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s*\((\d+)\)",
            full_text,
            re.IGNORECASE | re.DOTALL
        )

        runs = 0
        balls = 0

        if batting_match:
            runs = safe_int(batting_match.group(1))
            balls = safe_int(batting_match.group(2))

        # =================================================
        # 4s / 6s
        # =================================================

        fours_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s+4s",
            full_text,
            re.IGNORECASE
        )

        sixes_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s+6s",
            full_text,
            re.IGNORECASE
        )

        fours = safe_int(fours_match.group(1)) if fours_match else 0
        sixes = safe_int(sixes_match.group(1)) if sixes_match else 0

        # =================================================
        # WICKETS
        # =================================================

        wicket_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s*w",
            full_text,
            re.IGNORECASE
        )

        wickets = safe_int(wicket_match.group(1)) if wicket_match else 0

        strike_rate = round(
            (runs / balls) * 100,
            2
        ) if balls > 0 else 0

        return {
            "Match PDF": os.path.basename(pdf_path),
            "Runs": runs,
            "Balls": balls,
            "4s": fours,
            "6s": sixes,
            "Strike Rate": strike_rate,
            "Wickets": wickets
        }

    except Exception as e:

        st.warning(f"Failed to read {pdf_path}")

        return None


# =====================================================
# BUTTON
# =====================================================

if st.button("🚀 Analyze Scorecards"):

    if not os.path.exists(PDF_FOLDER):

        st.error("scorecards folder not found")

    else:

        pdf_files = [
            os.path.join(PDF_FOLDER, file)
            for file in os.listdir(PDF_FOLDER)
            if file.endswith(".pdf")
        ]

        st.success(f"Found {len(pdf_files)} PDF scorecards")

        all_stats = []

        progress = st.progress(0)

        for idx, pdf_file in enumerate(pdf_files):

            progress.progress((idx + 1) / len(pdf_files))

            data = extract_stats_from_pdf(pdf_file)

            if data:
                all_stats.append(data)

        if len(all_stats) == 0:

            st.error("No stats found.")

        else:

            df = pd.DataFrame(all_stats)

            # =============================================
            # METRICS
            # =============================================

            total_matches = len(df)
            total_runs = df["Runs"].sum()
            total_wickets = df["Wickets"].sum()
            highest_score = df["Runs"].max()
            total_4s = df["4s"].sum()
            total_6s = df["6s"].sum()

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Matches", total_matches)
            c2.metric("Runs", total_runs)
            c3.metric("Wickets", total_wickets)
            c4.metric("Highest", highest_score)

            c5, c6 = st.columns(2)

            c5.metric("Total 4s", total_4s)
            c6.metric("Total 6s", total_6s)

            st.divider()

            # =============================================
            # TABLE
            # =============================================

            st.subheader("📋 Match-by-Match Stats")

            st.dataframe(df, use_container_width=True)

            # =============================================
            # RUNS CHART
            # =============================================

            st.subheader("📈 Runs Per Match")

            fig = px.bar(
                df,
                x="Match PDF",
                y="Runs"
            )

            st.plotly_chart(fig, use_container_width=True)

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
