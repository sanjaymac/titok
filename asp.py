import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime, timedelta

def get_tiktok_data(url, use_vpn=False):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"URL": url, "Play Count": None, "Create Time (IST)": None}

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='SIGI_STATE')
        if not script_tag:
            return {"URL": url, "Play Count": None, "Create Time (IST)": None}

        json_data = json.loads(script_tag.string)
        video_data = next(iter(json_data.get('ItemModule', {}).values()), {})
        play_count = video_data.get('stats', {}).get('playCount')
        create_time = video_data.get('createTime')

        # Convert to IST
        if create_time:
            utc_time = datetime.utcfromtimestamp(int(create_time))
            ist_time = utc_time + timedelta(hours=5, minutes=30)
            ist_time_str = ist_time.strftime('%d/%m/%y %H:%M:%S')
        else:
            ist_time_str = None

        return {
            "URL": url,
            "Play Count": play_count,
            "Create Time (IST)": ist_time_str
        }

    except Exception as e:
        return {"URL": url, "Play Count": None, "Create Time (IST)": None}

# ------------------- Streamlit App ------------------- #

st.title("TikTok Metadata Extractor")

urls_input = st.text_area("Enter TikTok video URLs (one per line):")
use_vpn = st.checkbox("Check if using VPN")

if st.button("Run Scraper"):
    if urls_input.strip():
        urls = [url.strip() for url in urls_input.strip().split('\n') if url.strip()]
        
        total_urls = len(urls)
        progress_text = st.empty()
        results = []

        for index, url in enumerate(urls):
            data = get_tiktok_data(url, use_vpn)
            results.append(data)
            progress_text.text(f"Processing {index + 1}/{total_urls} URLs...")

        df = pd.DataFrame(results)
        st.dataframe(df)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="tiktok_metadata.csv", mime="text/csv")
    else:
        st.warning("Please enter at least one TikTok URL.")
