import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
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
        html_text = str(soup)

        play_count_match = re.search(r'"playCount":(\d+),', html_text)
        create_time_match = re.search(r'"createTime":"?(\d+)"?,', html_text)

        play_count = play_count_match.group(1) if play_count_match else None
        create_time = create_time_match.group(1) if create_time_match else None

        # Convert create_time to IST timezone
        if create_time:
            utc_time = datetime.utcfromtimestamp(int(create_time))
            ist_time = utc_time + timedelta(hours=5, minutes=30)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            ist_time_str = None

        return {
            "URL": url,
            "Play Count": play_count,
            "Create Time (IST)": ist_time_str
        }

    except Exception as e:
        return {"URL": url, "Play Count": None, "Create Time (IST)": None}

# Streamlit app
st.title("Bulk TikTok Play Count & Creation Time Scraper")

# Multi-line text input for multiple URLs
urls_input = st.text_area("Enter TikTok video URLs (one per line):")
use_vpn = st.checkbox("Check if using VPN")

if st.button("Run Scraper"):
    if urls_input.strip():
        urls = [url.strip() for url in urls_input.strip().split('\n') if url.strip()]
        
        total_urls = len(urls)
        progress_bar = st.progress(0)  # Initialize progress bar
        results = []

        for index, url in enumerate(urls):
            data = get_tiktok_data(url, use_vpn)
            results.append(data)

            # Update the progress bar
            progress_bar.progress((index + 1) / total_urls)
            st.text(f"Processing {index + 1}/{total_urls} URLs...")  # Show progress in text

        # Display results in a table
        df = pd.DataFrame(results)
        st.dataframe(df)

        # Optionally allow download
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="tiktok_data.csv", mime="text/csv")

    else:
        st.warning("Please enter at least one TikTok URL.")
