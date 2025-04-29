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

        html_text = response.text
        soup = BeautifulSoup(html_text, 'html.parser')

        play_count = None
        create_time = None

        # 1) Try TikTok __NEXT_DATA__ JSON
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data and next_data.string:
            try:
                data = json.loads(next_data.string)
                item = (data.get('props', {})
                            .get('pageProps', {})
                            .get('itemInfo', {})
                            .get('itemStruct', {}))
                stats = item.get('stats', {})
                if stats:
                    play_count = stats.get('playCount')
                if 'createTime' in item:
                    create_time = item.get('createTime')
            except (json.JSONDecodeError, AttributeError):
                pass

        # 2) Fallback to SIGI_STATE JSON if still missing
        if play_count is None or create_time is None:
            sigi = None
            for s in soup.find_all('script'):
                if s.string and 'SIGI_STATE' in s.string:
                    sigi = s.string
                    break
            if sigi:
                m = re.search(r"window\['SIGI_STATE'\]\s*=\s*({.*?})\s*;", sigi, flags=re.DOTALL)
                if m:
                    try:
                        data2 = json.loads(m.group(1))
                        item_module = data2.get('ItemModule', {})
                        if item_module:
                            vid = next(iter(item_module.values()))
                            stats2 = vid.get('stats', {})
                            if play_count is None:
                                play_count = stats2.get('playCount')
                            if create_time is None:
                                create_time = vid.get('createTime')
                    except json.JSONDecodeError:
                        pass

        # 3) Final regex fallback
        if play_count is None:
            m_play = re.search(r'"playCount"\s*:\s*(\d+)', html_text)
            if m_play:
                play_count = int(m_play.group(1))
        if create_time is None:
            m_time = re.search(r'"createTime"\s*:\s*"?(\d+)"?', html_text)
            if m_time:
                create_time = int(m_time.group(1))

        # Convert create_time to IST
        ist_time_str = None
        if create_time:
            utc = datetime.utcfromtimestamp(int(create_time))
            ist = utc + timedelta(hours=5, minutes=30)
            ist_time_str = ist.strftime('%d/%m/%y %H:%M:%S')

        return {"URL": url, "Play Count": play_count, "Create Time (IST)": ist_time_str}

    except Exception:
        return {"URL": url, "Play Count": None, "Create Time (IST)": None}

# Streamlit app
st.title("TikTok MetaData Retriever")
urls_input = st.text_area("Enter TikTok video URLs (one per line):")
use_vpn = st.checkbox("Check if using VPN")
if st.button("Run Scraper"):
    if urls_input.strip():
        urls = [u.strip() for u in urls_input.splitlines() if u.strip()]
        total = len(urls)
        progress = st.empty()
        results = []
        for i, url in enumerate(urls, 1):
            results.append(get_tiktok_data(url, use_vpn))
            progress.text(f"Processing {i}/{total} URLs...")
        df = pd.DataFrame(results)
        st.dataframe(df)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="tiktok_data.csv", mime="text/csv")
    else:
        st.warning("Please enter at least one TikTok URL.")
