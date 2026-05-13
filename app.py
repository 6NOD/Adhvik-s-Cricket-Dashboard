# =========================================================
# CricHeroes Player Stats Scraper + Streamlit Dashboard
# Player: Adhvik R
# =========================================================
#
# INSTALL:
#
# pip install streamlit playwright pandas beautifulsoup4 lxml plotly
# playwright install
#
# RUN:
#
# streamlit run app.py
#
# =========================================================

import re
import time
import pandas as pd
import streamlit as st
import plotly.express as px

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# =========================================================
# CONFIG
# =========================================================

PLAYER_NAME = "Adhvik R"
PROFILE_URL = "https://cricheroes.com/player-profile/30388801/adhvik-r/matches"

HEADLESS = True
WAIT_TIME = 4000

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Adhvik Cricket Dashboard",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 Adhvik Cricket Analytics Dashboard")

# =========================================================
# HELPERS
# =========================================================

def safe_int(value):
    try:
        return int(value)
    except:
        return 0


def extract_match_links(page):

    st.info("Loading CricHeroes profile...")

    page.goto(PROFILE_URL, timeout=120000)

    page.wait_for_timeout(6000)

    html = page.content()

    soup = BeautifulSoup(html, "lxml")

    links = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/scorecard/" in href or "/match/" in href:

            if href.startswith("http"):
                full_link = href
            else:
                full_link = "https://cricheroes.com" + href

            if full_link not in links:
                links.append(full_link)

    links = list(set(links))

    return links


def extract_match_data(page, match_url):

    try:

        page.goto(match_url, timeout=120000)

        page.wait_for_timeout(WAIT_TIME)

        html = page.content()

        soup = BeautifulSoup(html, "lxml")

        text = soup.get_text("\n")

        if PLAYER_NAME.lower() not in text.lower():
            return None

        # =====================================================
        # BASIC MATCH TITLE
        # =====================================================

        title = soup.title.text if soup.title else "Unknown Match"

        # =====================================================
        # BATTING REGEX
        # Example pattern:
        # Adhvik 45(32)
        # =====================================================

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

        # =====================================================
        # 4s and 6s
        # =====================================================

        fours_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s+4s",
            text,
            re.IGNORECASE | re.DOTALL
        )

        sixes_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s+6s",
            text,
            re.IGNORECASE | re.DOTALL
        )

        fours = safe_int(fours_match.group(1)) if fours_match else 0
        sixes = safe_int(sixes_match.group(1)) if sixes_match else 0

        # =====================================================
        # WICKETS
        # =====================================================

        wicket_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s*w",
            text,
            re.IGNORECASE
        )

        wickets = safe_int(wicket_match.group(1)) if wicket_match else 0

        # =====================================================
        # OVERS
        # =====================================================

        overs_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+\.\d+)\s*ov",
            text,
            re.IGNORECASE
        )

        overs = float(overs_match.group(1)) if overs_match else 0

        # =====================================================
        # STRIKE RATE
        # =====================================================

        strike_rate = round((runs / balls) * 100, 2) if balls > 0 else 0

        return {
            "Match": title,
            "Runs": runs,
            "Balls": balls,
            "4s": fours,
            "6s": sixes,
            "Strike Rate": strike_rate,
            "Wickets": wickets,
            "Overs": overs,
            "URL": match_url
        }

    except Exception as e:

        st.warning(f"Failed: {match_url}")

        return None


# =========================================================
# SCRAPE BUTTON
# =========================================================

if st.button("🚀 Fetch Adhvik Stats"):

    all_stats = []

    progress = st.progress(0)

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=HEADLESS)

        page = browser.new_page()

        match_links = extract_match_links(page)

        st.success(f"Found {len(match_links)} possible matches")

        for idx, link in enumerate(match_links):

            progress.progress((idx + 1) / len(match_links))

            result = extract_match_data(page, link)

            if result:
                all_stats.append(result)

            time.sleep(2)

        browser.close()

    # =====================================================
    # DATAFRAME
    # =====================================================

    if len(all_stats) == 0:

        st.error("No stats found.")

    else:

        df = pd.DataFrame(all_stats)

        # =================================================
        # SUMMARY STATS
        # =================================================

        total_matches = len(df)

        total_runs = df["Runs"].sum()

        total_wickets = df["Wickets"].sum()

        total_4s = df["4s"].sum()

        total_6s = df["6s"].sum()

        batting_average = round(
            total_runs / total_matches,
            2
        ) if total_matches > 0 else 0

        avg_sr = round(
            df["Strike Rate"].mean(),
            2
        )

        highest_score = df["Runs"].max()

        # =================================================
        # METRICS
        # =================================================

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Matches", total_matches)
        c2.metric("Runs", total_runs)
        c3.metric("Wickets", total_wickets)
        c4.metric("Highest", highest_score)

        c5, c6, c7 = st.columns(3)

        c5.metric("Bat Avg", batting_average)
        c6.metric("Avg SR", avg_sr)
        c7.metric("4s / 6s", f"{total_4s} / {total_6s}")

        st.divider()

        # =================================================
        # MATCH TABLE
        # =================================================

        st.subheader("📋 Match-by-Match Stats")

        st.dataframe(
            df.sort_values(by="Runs", ascending=False),
            use_container_width=True
        )

        # =================================================
        # RUNS CHART
        # =================================================

        st.subheader("📈 Runs Per Match")

        fig_runs = px.bar(
            df,
            x="Match",
            y="Runs",
            hover_data=["Strike Rate"]
        )

        st.plotly_chart(fig_runs, use_container_width=True)

        # =================================================
        # WICKETS CHART
        # =================================================

        st.subheader("🎯 Wickets Per Match")

        fig_wickets = px.bar(
            df,
            x="Match",
            y="Wickets"
        )

        st.plotly_chart(fig_wickets, use_container_width=True)

        # =================================================
        # DOWNLOAD CSV
        # =================================================

        csv = df.to_csv(index=False)

        st.download_button(
            "⬇ Download CSV",
            csv,
            file_name="adhvik_stats.csv",
            mime="text/csv"
        )

        st.success("Dashboard generated successfully.")
