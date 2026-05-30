import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="도윤이의 KBO 기록 검색기", page_icon="⚾", layout="wide")

# ==========================================
# ⭐ 배경 사진 적용 (제공해주신 깃허브 주소 반영)
# ==========================================
background_image_url = "https://github.com/audskal1847/kbo-dashboard/blob/main/KakaoTalk_20260531_064816799.jpg?raw=true"

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("{background_image_url}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}
/* 사진을 연하게 만들기 위해 반투명한 흰색 도화지를 위에 덮어줍니다 */
[data-testid="stAppViewContainer"]::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background-color: rgba(255, 255, 255, 0.95); /* 0.85는 흰색의 진한 정도입니다. (0.0~1.0) */
    z-index: -1;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==========================================
# 2. 사이드바 (Sidebar) 메뉴 구성
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/ko/8/82/KBO_%EB%A1%9C%EA%B3%A0.svg", width=150)
    st.header("📊 데이터 메뉴")
    
    menu = st.radio(
        "원하시는 항목을 선택하세요:",
        [
            "🔍 도윤이의 선수 검색기", 
            "🏃 타자 순위 (Top 30)", 
            "⚾ 투수 순위 (Top 30)", 
            "🏟️ 관중 현황",
            "📜 역대 기록 (구단)", 
            "📜 역대 기록 (타자)",
            "📜 역대 기록 (투수)"
        ]
    )

# ==========================================
# 3. 데이터 가공 함수 
# ==========================================
def format_kbo_table(df):
    cols_to_drop = [col for col in df.columns if 'Unnamed' in str(col)]
    df.drop(columns=cols_to_drop, inplace=True)
    df.dropna(how='all', inplace=True)
    
    kor_columns = {
        'AVG': '타율', 'G': '경기', 'PA': '타석', 'AB': '타수', 
        'R': '득점', 'H': '안타', '2B': '2루타', '3B': '3루타', 
        'HR': '홈런', 'TB': '루타', 'RBI': '타점', 'SB': '도루', 
        'CS': '실패', 'BB': '볼넷', 'HBP': '사구', 'SO': '삼진', 
        'GDP': '병살', 'SLG': '장타율', 'OBP': '출루율', 'E': '실책',
        'SAC': '희번', 'SF': '희플',
        'ERA': '평균자책', 'W': '승리', 'L': '패배', 'SV': '세이브', 
        'HLD': '홀드', 'WPCT': '승률', 'IP': '이닝', 'ER': '자책점',
        'CG': '완투', 'SHO': '완봉', 'QS': 'QS', 'BS': '블론',
        'WHIP': 'WHIP', 'NP': '투구수'
    }
    df.rename(columns=kor_columns, inplace=True)
    
    format_cols = ['타율', '장타율', '출루율', '평균자책', '평균자책점', '승률']
    for col in format_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').map('{:.3f}'.format)
            
    return df

# ==========================================
# 4. 공통 크롤링 실행 함수 
# ==========================================
def fetch_and_display_data(title, url, loading_msg="데이터를 불러오는 중입니다..."):
    st.title(title)
    with st.spinner(loading_msg):
        try:
            response = requests.get(url, headers=headers)
            tables = pd.read_html(io.StringIO(response.text), flavor=['lxml', 'html5lib'])
            
            for tbl in tables:
                df = format_kbo_table(tbl)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
        except ValueError as e:
            if "No tables found" in str(e):
                st.warning("⚠️ 현재 홈페이지에서 해당 데이터를 텍스트 표로 제공하지 않고 있습니다.")
            else:
                st.error(f"데이터 해석 중 오류가 발생했습니다: {e}")
        except Exception as e:
            st.error(f"인터넷 연결 등 문제가 발생했습니다: {e}")

# ==========================================
# 5. 메뉴별 기능 매핑
# ==========================================
if menu == "🔍 도윤이의 선수 검색기":
    st.title("⚾ 도윤이의 KBO 기록 검색기") 
    st.markdown("선수 이름(예: 양현종, 구자욱)을 입력하면 동명이인까지 모두 찾아 기록을 보여줍니다.")
    
    name = st.text_input("검색할 선수 이름을 입력하세요")

    if st.button("기록 검색하기", type="primary"):
        if name:
            with st.spinner(f"'{name}' 선수의 기록을 찾는 중..."):
                try:
                    search_url = f"https://www.koreabaseball.com/Player/Search.aspx?searchWord={name}"
                    response = requests.get(search_url, headers=headers)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    player_links = soup.find_all('a', href=lambda href: href and 'playerId=' in href)
                    
                    if not player_links:
                        st.error(f"'{name}' 선수를 찾을 수 없습니다.")
                    else:
                        unique_links = []
                        seen_hrefs = set()
                        for a in player_links:
                            href = a['href']
                            if href not in seen_hrefs:
                                unique_links.append(href)
                                seen_hrefs.add(href)
                        
                        st.success(f"성공! 총 {len(unique_links)}명의 '{name}' 선수를 찾았습니다.")
                        
                        for i, href in enumerate(unique_links):
                            detail_url = "https://www.koreabaseball.com" + href
                            detail_response = requests.get(detail_url, headers=headers)
                            tables = pd.read_html(io.StringIO(detail_response.text))
                            
                            player_stats = format_kbo_table(tables[0])
                            
                            st.markdown(f"#### 👤 {name} 선수 (검색결과 {i+1})")
                            st.dataframe(player_stats, use_container_width=True, hide_index=True)
                            st.markdown("---")
                        
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
        else:
            st.warning("선수 이름을 먼저 입력해주세요.")

elif menu == "🏃 타자 순위 (Top 30)":
    fetch_and_display_data("🏃 타자 순위 (Top 30)", "https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx")

elif menu == "⚾ 투수 순위 (Top 30)":
    fetch_and_display_data("⚾ 투수 순위 (Top 30)", "https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx")

elif menu == "🏟️ 관중 현황":
    fetch_and_display_data("🏟️ 구단별 관중 현황", "https://www.koreabaseball.com/Record/Crowd/GraphDaily.aspx")

elif menu == "📜 역대 기록 (구단)":
    st.title("📜 역대 구단 성적")
    st.markdown("원하시는 년대를 선택하시면 해당 기간의 구단 성적을 확인하실 수 있습니다.")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["2020년대", "2010년대", "2000년대", "1990년대", "1980년대", "전,후기순위"])
    
    tab_urls = [
        ("2020년대", "https://www.koreabaseball.com/Record/History/Team/Record.aspx"),
        ("2010년대", "https://www.koreabaseball.com/Record/History/Team/Record.aspx?startYear=2010&halfSc=T"),
        ("2000년대", "https://www.koreabaseball.com/Record/History/Team/Record.aspx?startYear=2000&halfSc=T"),
        ("1990년대", "https://www.koreabaseball.com/Record/History/Team/Record.aspx?startYear=1990&halfSc=T"),
        ("1980년대", "https://www.koreabaseball.com/Record/History/Team/Record.aspx?startYear=1980&halfSc=T"),
        ("전,후기순위", "https://www.koreabaseball.com/Record/History/Team/Record.aspx?startYear=1980&halfSc=FS")
    ]
    
    for tab, (tab_name, url) in zip([tab1, tab2, tab3, tab4, tab5, tab6], tab_urls):
        with tab:
            with st.spinner(f"{tab_name} 데이터를 불러오는 중입니다..."):
                try:
                    response = requests.get(url, headers=headers)
                    tables = pd.read_html(io.StringIO(response.text), flavor=['lxml', 'html5lib'])
                    
                    if not tables:
                        st.warning("데이터가 없습니다.")
                    else:
                        for tbl in tables:
                            df = format_kbo_table(tbl)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")

elif menu == "📜 역대 기록 (타자)":
    fetch_and_display_data("📜 역대 기록 (타자 부문)", "https://www.koreabaseball.com/Record/History/Top/Hitter.aspx")

elif menu == "📜 역대 기록 (투수)":
    fetch_and_display_data("📜 역대 기록 (투수 부문)", "https://www.koreabaseball.com/Record/History/Top/Pitcher.aspx")
