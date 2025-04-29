import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from datetime import datetime, timedelta


def get_tiktok_data(url, use_vpn=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"URL": url, "Play Count": None, "Create Time (IST)": None}

        html_text = response.text
        soup = BeautifulSoup(html_text, 'html.parser')

        play_count = None
        create_time = None

        # Attempt to extract JSON from TikTok's SIGI_STATE script
        sigi_script = None
        for script in soup.find_all('script'):
            if script.string and 'SIGI_STATE' in script.string:
                sigi_script = script.string
                break
        if sigi_script:
            # Extract JSON object from the JS assignment
            m = re.search(r"window\['SIGI_STATE'\]\s*=\s*({.*?})\s*;", sigi_script, flags=re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    item_module = data.get('ItemModule', {})
                    if item_module:
                        # grab first video's stats
                        video_info = next(iter(item_module.values()))
                        stats = video_info.get('stats', {})
                        play_count = int(stats.get('playCount', 0)) if stats.get('playCount') else None
                        create_time = int(video_info.get('createTime')) if video_info.get('createTime') else None
                except json.JSONDecodeError:
                    pass

        # Fallback regex if JSON parse failed
        if play_count is None:
            m_play = re.search(r'"playCount"\s*:\s*(\d+)', html_text)
            if m_play:
                play_count = int(m_play.group(1))

        if create_time is None:
            m_create = re.search(r'"createTime"\s*:\s*"?(\d+)"?', html_text)
            if m_create:
                create_time = int(m_create.group(1))

        # Convert create_time to IST timezone
        ist_time_str = None
        if create_time:
            utc_time = datetime.utcfromtimestamp(create_time)
            ist_time = utc_time + timedelta(hours=5, minutes=30)
            ist_time_str = ist_time.strftime('%d/%m/%y %H:%M:%S')

        return {
            "URL": url,
            "Play Count": play_count,
            "Create Time (IST)": ist_time_str
        }

    except Exception:
        return {"URL": url, "Play Count": None, "Create Time (IST)": None}

# Streamlit app
st.title("TikTok MetaData Retriever")
urls_input = st.text_area("Enter TikTok video URLs (one per line):")
use_vpn = st.checkbox("Check if using VPN")

if st.button("Run Scraper"):
    if urls_input.strip():
        urls = [u.strip() for u in urls_input.splitlines() if u.strip()]
        total = len(urls)
        progress = st.empty()
        results = []
        for idx, url in enumerate(urls, start=1):
            results.append(get_tiktok_data(url, use_vpn))
            progress.text(f"Processing {idx}/{total} URLs...")

        df = pd.DataFrame(results)
        st.dataframe(df)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="tiktok_data.csv", mime="text/csv")
    else:
        st.warning("Please enter at least one TikTok URL.")
