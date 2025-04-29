# TikTok MetaData Retriever using TikTokApi with fallback scraping
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from datetime import datetime, timedelta

# Requires: pip install TikTokApi
from TikTokApi import TikTokApi


def get_tiktok_data(url, use_vpn=False):
    """
    Fetches play count and creation time from a TikTok video URL.
    Primary method: TikTokApi library.
    Fallback: HTML parsing (NextData, SIGI_STATE, regex).
    """
    play_count = None
    create_time = None
    video_id = url.rstrip('/').split('/')[-1].split('?')[0]

    # 1) Primary: use TikTokApi
    try:
        with TikTokApi() as api:
            video = api.video(id=video_id)
            info = video.info()
            stats = info.get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
            play_count = stats.get('playCount')
            create_time = info['itemInfo']['itemStruct'].get('createTime')
    except Exception:
        play_count = None
        create_time = None

    # 2) Fallback scraping if library fails
    if play_count is None or create_time is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')

            # Try __NEXT_DATA__
            nd = soup.find('script', id='__NEXT_DATA__')
            if nd and nd.string:
                data = json.loads(nd.string)
                item = (data.get('props', {})
                           .get('pageProps', {})
                           .get('itemInfo', {})
                           .get('itemStruct', {}))
                stats = item.get('stats', {})
                play_count = play_count or stats.get('playCount')
                create_time = create_time or item.get('createTime')

            # Try SIGI_STATE
            if play_count is None or create_time is None:
                for script in soup.find_all('script'):
                    if script.string and 'SIGI_STATE' in script.string:
                        m = re.search(r"window\['SIGI_STATE'\]\s*=\s*({.*?})\s*;", script.string, flags=re.DOTALL)
                        if m:
                            data2 = json.loads(m.group(1))
                            im = data2.get('ItemModule', {})
                            if im:
                                vid = next(iter(im.values()))
                                stats2 = vid.get('stats', {})
                                play_count = play_count or stats2.get('playCount')
                                create_time = create_time or vid.get('createTime')
                        break

            # Regex fallback
            if play_count is None:
                m1 = re.search(r'"playCount"\s*:\s*(\d+)', html)
                if m1:
                    play_count = int(m1.group(1))
            if create_time is None:
                m2 = re.search(r'"createTime"\s*:\s*"?(\d+)"?', html)
                if m2:
                    create_time = int(m2.group(1))

        except Exception:
            pass

    # Convert timestamp to IST string
    ist_str = None
    if create_time:
        utc = datetime.utcfromtimestamp(int(create_time))
        ist = utc + timedelta(hours=5, minutes=30)
        ist_str = ist.strftime('%d/%m/%y %H:%M:%S')

    return {"URL": url, "Play Count": play_count, "Create Time (IST)": ist_str}

# Streamlit UI
st.title("TikTok MetaData Retriever")
urls = st.text_area("Enter TikTok video URLs (one per line):")
use_vpn = st.checkbox("Check if using VPN")  # placeholder for future VPN support
if st.button("Run Scraper"):
    if not urls.strip():
        st.warning("Please enter at least one TikTok URL.")
    else:
        url_list = [u.strip() for u in urls.splitlines() if u.strip()]
        results = []
        prog = st.empty()
        total = len(url_list)
        for i, u in enumerate(url_list, 1):
            results.append(get_tiktok_data(u, use_vpn))
            prog.text(f"Processing {i}/{total}...")
        df = pd.DataFrame(results)
        st.dataframe(df)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "tiktok_data.csv", "text/csv")
