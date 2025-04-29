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

        soup = BeautifulSoup(response.content, 'html.parser')

        # Attempt JSON parse from TikTok's embedded state
        play_count = None
        create_time = None
        state_script = soup.find('script', id='SIGI_STATE')
        if state_script and state_script.string:
            try:
                data = json.loads(state_script.string)
                # Navigate to video data (ItemModule contains video stats)
                item_module = data.get('ItemModule', {})
                # There may be multiple keys; pick the first video
                if item_module:
                    video_info = next(iter(item_module.values()))
                    stats = video_info.get('stats', {})
                    play_count = stats.get('playCount')
                    create_time = video_info.get('createTime')
            except (json.JSONDecodeError, StopIteration):
                # Fallback to regex
                pass

        # Fallback regex for playCount
        if play_count is None:
            m = re.search(r'"playCount"\s*:\s*(\d+)', response.text)
            if m:
                play_count = int(m.group(1))

        # Fallback regex for createTime
        if create_time is None:
            m2 = re.search(r'"createTime"\s*:\s*"?(\d+)"?', response.text)
            if m2:
                create_time = int(m2.group(1))

        # Convert create_time to IST timezone
        ist_time_str = None
        if create_time:
            utc_time = datetime.utcfromtimestamp(int(create_time))
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
        urls = [url.strip() for url in urls_input.splitlines() if url.strip()]
        total_urls = len(urls)
        progress_text = st.empty()
        results = []

        for idx, url in enumerate(urls, 1):
            data = get_tiktok_data(url, use_vpn)
            results.append(data)
            progress_text.text(f"Processing {idx}/{total_urls} URLs...")

        df = pd.DataFrame(results)
        st.dataframe(df)

        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="tiktok_data.csv", mime="text/csv")
    else:
        st.warning("Please enter at least one TikTok URL.")
