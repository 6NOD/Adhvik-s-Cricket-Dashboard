import re
import pandas as pd
import requests
import streamlit as st
import plotly.express as px

from bs4 import BeautifulSoup

# =====================================================
# CONFIG
# =====================================================

PLAYER_NAME = "Adhvik"

MATCH_URLS = [

    "https://cricheroes.com/scorecard/24597615/rsca-summer-cup-(2026-u-14)/rsca-guwahati-exp-vs-rsca-chalukya-exp/scorecard",

    "https://cricheroes.com/scorecard/24556677/baxter-premier-league-2026/nova-super-challengers-vs-rapid-responders/scorecard",

    "https://cricheroes.com/scorecard/24556423/baxter-premier-league-2026/nova-super-challengers-vs-quantum-ke-dhurandar/summary"

]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================================================
# PAGE CONFIG
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
# EXTRACT PLAYER STATS
# =====================================================

def extract_match_data(match_url):

    try:

        response = requests.get(match_url, headers=HEADERS)

        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text("\n")

        if PLAYER_NAME.lower() not in text.lower():
            return None

        title = soup.title.text if soup.title else "Unknown Match"

        # =================================================
        # RUNS + BALLS
        # =================================================

        batting_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\((\d+)\)",
            text,
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
            text,
            re.IGNORECASE
        )

        sixes_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s+6s",
            text,
            re.IGNORECASE
        )

        fours = safe_int(fours_match.group(1)) if fours_match else 0
        sixes = safe_int(sixes_match.group(1)) if sixes_match else 0

        # =================================================
        # WICKETS
        # =================================================

        wicket_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s*w",
            text,
            re.IGNORECASE
        )

        wickets = safe_int(wicket_match.group(1)) if wicket_match else 0

        strike_rate = round(
            (runs / balls) * 100,
            2
        ) if balls > 0 else 0

        return {
            "Match": title,
            "Runs": runs,
            "Balls": balls,
            "4s": fours,
            "6s": sixes,
            "Strike Rate": strike_rate,
            "Wickets": wickets,
            "URL": match_url
        }

    except Exception as e:

        st.warning(f"Failed: {match_url}")

        return None

# =====================================================
# BUTTON
# =====================================================

if st.button("🚀 Fetch Stats"):

    all_stats = []

    progress = st.progress(0)

    for idx, url in enumerate(MATCH_URLS):

        progress.progress((idx + 1) / len(MATCH_URLS))

        data = extract_match_data(url)

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

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Matches", total_matches)
        c2.metric("Runs", total_runs)
        c3.metric("Wickets", total_wickets)
        c4.metric("Highest", highest_score)

        st.divider()

        # =============================================
        # TABLE
        # =============================================

        st.subheader("📋 Match Stats")

        st.dataframe(df, use_container_width=True)

        # =============================================
        # RUNS CHART
        # =============================================

        st.subheader("📈 Runs Per Match")

        fig = px.bar(
            df,
            x="Match",
            y="Runs"
        )

        st.plotly_chart(fig, use_container_width=True)

        # =============================================
        # DOWNLOAD
        # =============================================

        csv = df.to_csv(index=False)

        st.download_button(
            "⬇ Download CSV",
            csv,
            file_name="adhvik_stats.csv",
            mime="text/csv"
        )
