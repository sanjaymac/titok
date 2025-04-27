import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Function to fetch video details from TikTok page
def fetch_tiktok_details(url):
    # Set headers to simulate a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Send the request to TikTok URL
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Error fetching the URL: {e}")
        return None

    # Parse the HTML page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Search for the embedded JSON data
    json_data = None
    for script in soup.find_all('script'):
        if 'window.__INIT_PROPS__' in script.text:
            json_text = script.text.strip().replace('window.__INIT_PROPS__=', '')
            try:
                json_data = json.loads(json_text)
            except json.JSONDecodeError:
                pass
            break

    # If no JSON data is found, return None
    if json_data is None:
        st.error("Could not find video data on this page.")
        return None

    # Extract video stats and creation time
    try:
        play_count = json_data['props']['pageProps']['itemInfo']['itemStruct']['stats']['playCount']
        create_time_timestamp = int(json_data['props']['pageProps']['itemInfo']['itemStruct']['createTime'])

        # Convert the timestamp to a human-readable format
        create_time = datetime.utcfromtimestamp(create_time_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        return play_count, create_time
    except KeyError:
        st.error("Could not extract the necessary video details.")
        return None

# Streamlit UI
st.title('TikTok Video Stats')

# Input field for TikTok URL
url = st.text_input("Enter TikTok Video URL")

if url:
    # Fetch video details from TikTok
    details = fetch_tiktok_details(url)

    if details:
        play_count, create_time = details
        st.write(f"**Play Count:** {play_count}")
        st.write(f"**Create Time:** {create_time}")
    else:
        st.write("Could not fetch video details. Please check the URL and try again.")
