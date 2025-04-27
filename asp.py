import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

st.set_page_config(page_title="TikTok Video Info Scraper", page_icon="🎵", layout="centered")

st.title("🎵 TikTok Video Info Scraper (Desktop with BeautifulSoup)")
st.write("Enter a TikTok video URL below:")

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
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find the script with id="SIGI_STATE"
                script_tag = soup.find('script', {'id': 'SIGI_STATE'})
                if not script_tag:
                    st.error("SIGI_STATE script not found. TikTok probably blocked the bot.")
                else:
                    json_text = script_tag.string

                    # Parse the JSON safely
                    try:
                        data = json.loads(json_text)

                        # Extract video ID
                        video_id_match = re.search(r'/video/(\d+)', url)
                        if not video_id_match:
                            st.error("Could not extract video ID from URL.")
                        else:
                            video_id = video_id_match.group(1)

                            video_data = data.get('ItemModule', {}).get(video_id)
                            if not video_data:
                                st.error("Video data not found inside SIGI_STATE JSON.")
                            else:
                                play_count = video_data['stats']['playCount']
                                create_time = int(video_data['createTime'])
                                upload_date = datetime.utcfromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')

                                st.success("Video Details Found 🎯")
                                st.write(f"**Play Count:** {play_count}")
                                st.write(f"**Upload Date (UTC):** {upload_date}")

                    except json.JSONDecodeError as e:
                        st.error(f"Failed to parse SIGI_STATE JSON: {e}")

        except Exception as e:
            st.error(f"An error occurred: {e}")
