import streamlit as st
import requests
import re
import json
from datetime import datetime

st.set_page_config(page_title="TikTok Video Info Scraper", page_icon="🎵", layout="centered")

st.title("🎵 TikTok Video Info Scraper (Normal Desktop Version)")
st.write("Enter a TikTok video URL below:")

# Input field
url = st.text_input("TikTok Video URL:")

if st.button("Fetch Info"):
    if not url:
        st.error("Please enter a TikTok video URL.")
    else:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/119.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                st.error(f"Failed to fetch page. Status code: {response.status_code}")
            else:
                content = response.text

                # Extract webapp.video-detail JSON
                match = re.search(r'"webapp\.video-detail":(\{.*?\})\s*,\s*"webapp\.search"', content, re.S)
                if not match:
                    st.error("Could not find 'webapp.video-detail' block.")
                else:
                    video_detail_json = json.loads(match.group(1))

                    item_struct = video_detail_json.get('itemInfo', {}).get('itemStruct')
                    if not item_struct:
                        st.error("Could not find itemStruct in video detail.")
                    else:
                        play_count = item_struct['stats']['playCount']
                        create_time = int(item_struct['createTime'])

                        upload_date = datetime.utcfromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')

                        st.success("Video Details Found 🎯")
                        st.write(f"**Play Count:** {play_count}")
                        st.write(f"**Upload Date (UTC):** {upload_date}")

        except Exception as e:
            st.error(f"Error: {e}")
