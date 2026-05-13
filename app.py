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

PROFILE_URL = "https://cricheroes.com/player-profile/30388801/adhvik-r/matches"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

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
# GET MATCH LINKS
# =====================================================

def get_match_links():

    response = requests.get(PROFILE_URL, headers=HEADERS)

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/match/" in href or "/scorecard/" in href:

            if href.startswith("http"):
                full_link = href
            else:
                full_link = "https://cricheroes.com" + href

            if full_link not in links:
                links.append(full_link)

    return list(set(links))


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

        # =============================================
        # BATTING
        # =============================================

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

        # =============================================
        # 4s / 6s
        # =============================================

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

        # =============================================
        # WICKETS
        # =============================================

        wicket_match = re.search(
            rf"{PLAYER_NAME}.*?(\d+)\s*w",
            text,
            re.IGNORECASE
        )

        wickets = safe_int(wicket_match.group(1)) if wicket_match else 0

        strike_rate = round((runs / balls) * 100, 2) if balls > 0 else 0

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

    except Exception:
        return None


# =====================================================
# MAIN BUTTON
# =====================================================

if st.button("🚀 Fetch Stats"):

    st.info("Fetching matches...")

    links = get_match_links()

    st.success(f"Found {len(links)} matches")

    all_stats = []

    progress = st.progress(0)

    for idx, link in enumerate(links):

        progress.progress((idx + 1) / len(links))

        data = extract_match_data(link)

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
        # CHART
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
