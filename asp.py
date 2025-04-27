import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Function to extract video details from TikTok page
def fetch_tiktok_details(url):
    # Make a request to the TikTok page
    response = requests.get(url)
    if response.status_code != 200:
        return None

    # Parse the page using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the JSON data embedded in the page (it's in a script tag)
    json_data = None
    for script in soup.find_all('script'):
        if 'window.__INIT_PROPS__' in script.text:
            # Extract JSON data from script
            json_text = script.text.strip().replace('window.__INIT_PROPS__=', '')
            try:
                json_data = json.loads(json_text)
            except json.JSONDecodeError:
                pass
            break

    # If no data found, return None
    if json_data is None:
        return None
    
    # Extract relevant details
    try:
        play_count = json_data['props']['pageProps']['itemInfo']['itemStruct']['stats']['playCount']
        create_time_timestamp = int(json_data['props']['pageProps']['itemInfo']['itemStruct']['createTime'])
        
        # Convert the timestamp to a human-readable format
        create_time = datetime.utcfromtimestamp(create_time_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        return play_count, create_time
    except KeyError:
        return None

# Streamlit app UI
st.title('TikTok Video Stats')

# Input for TikTok URL
url = st.text_input("Enter TikTok Video URL")

if url:
    # Fetch video details
    details = fetch_tiktok_details(url)
    
    if details:
        play_count, create_time = details
        st.write(f"**Play Count:** {play_count}")
        st.write(f"**Create Time:** {create_time}")
    else:
        st.write("Could not fetch video details. Please check the URL and try again.")
