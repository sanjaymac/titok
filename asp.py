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

        play_count_re = re.compile(r'''
            "playCount"      # the key
            \s*:\s*          # colon with any amount of space
            (\d+)            # capture one or more digits
        ''', re.VERBOSE)

# more flexible createTime: optional quotes around the number and optional trailing comma
        create_time_re = re.compile(r'''
            "createTime"     # the key
            \s*:\s*          # colon +/- whitespace
            "?(?P<ts>\d+)"?  # digits, maybe in quotes
            \s*,?            # maybe whitespace + comma
        ''', re.VERBOSE)

        play_count = play_count_re.group(1) if play_count_re else None
        create_time = create_time_re.group(1) if create_time_re else None

        # Convert create_time to IST timezone
        if create_time:
            utc_time = datetime.utcfromtimestamp(int(create_time))
            ist_time = utc_time + timedelta(hours=5, minutes=30)
            ist_time_str = ist_time.strftime('%d/%m/%y %H:%M:%S')  # Change format to DD/MM/YY HH:MM:SS
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
st.title("TikTok MetaData Retriever")

# Multi-line text input for multiple URLs
urls_input = st.text_area("Enter TikTok video URLs (one per line):")
use_vpn = st.checkbox("Check if using VPN")

if st.button("Run Scraper"):
    if urls_input.strip():
        urls = [url.strip() for url in urls_input.strip().split('\n') if url.strip()]
        
        total_urls = len(urls)
        progress_text = st.empty()  # Create an empty placeholder for progress text
        results = []

        for index, url in enumerate(urls):
            data = get_tiktok_data(url, use_vpn)
            results.append(data)

            # Update progress count in a single line
            progress_text.text(f"Processing {index + 1}/{total_urls} URLs...")

        # Display results in a table
        df = pd.DataFrame(results)
        st.dataframe(df)

        # Optionally allow download
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="tiktok_data.csv", mime="text/csv")

    else:
        st.warning("Please enter at least one TikTok URL.")
