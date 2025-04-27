import streamlit as st
from TikTokApi import TikTokApi
from datetime import datetime

# Initialize the TikTokApi
api = TikTokApi.get_instance()

# Function to fetch video details using the TikTok API
def fetch_tiktok_details(url):
    # Extract the video ID from the URL
    video_id = url.split("/")[-1]
    
    try:
        # Fetch the video by its ID
        video = api.get_video_by_id(video_id)
        
        # Extract stats and creation time
        play_count = video['stats']['playCount']
        create_time_timestamp = video['createTime']
        
        # Convert the timestamp to a human-readable format
        create_time = datetime.utcfromtimestamp(create_time_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        return play_count, create_time
    except Exception as e:
        st.error(f"Error fetching video details: {e}")
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
