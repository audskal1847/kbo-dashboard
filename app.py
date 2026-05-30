import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io  # <-- 새롭게 추가된 필수 도구 (텍스트를 파일처럼 다루게 해줌)

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="KBO 통합 데이터 센터", page_icon="⚾", layout="wide")

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
            "🔍 선수 상세 기록실 (통합)", 
            "🏆 정규시즌 팀 순위", 
            "🏃 타자 순위 (Top 30)", 
            "⚾ 투수 순위 (Top 30)", 
            "🏟️ 관중 현황",
            "📜 역대 기록 (타자)",
            "📜 역대 기록 (투수)",
            "🎯 예상 달성 기록"
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
    
    format_cols = ['타율', '장타율', '출루율', '평균자책', '승률']
    for col in format_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').map('{:.3f}'.format)
            
    return df

# ==========================================
# 4. 표 그리기 함수 
# ==========================================
def display_full_table(df):
    html_table = df.to_html(index=False, justify='center')
    
    custom_html = f"""
    <style>
        .kbo-table-wrapper {{
            width: 100%;
            overflow-x: auto; 
        }}
        .kbo-table-wrapper table {{
            width: 100%;
            font-size: 13px; 
            border-collapse: collapse;
            text-align: center;
        }}
        .kbo-table-wrapper th {{
            background-color: #f0f2f6;
            color: #333;
            padding: 8px 4px;
            border-bottom: 2px solid #bbb;
            white-space: nowrap; 
            font-weight: bold;
        }}
        .kbo-table-wrapper td {{
            padding: 6px 4px;
            border-bottom: 1px solid #ddd;
        }}
        .kbo-table-wrapper tr:hover {{
            background-color: #f9f9f9;
        }}
    </style>
    <div class="kbo-table-wrapper">
        {html_table}
    </div>
    """
    st.markdown(custom_html, unsafe_allow_html=True)


# ==========================================
# 5. 공통 크롤링 실행 함수 
# ==========================================
def fetch_and_display_data(title, url, loading_msg="데이터를 불러오는 중입니다..."):
    st.title(title)
    with st.spinner(loading_msg):
        try:
            response = requests.get(url, headers=headers)
            # ⭐ 수정됨: io.StringIO()를 사용하여 안전하게 텍스트 전달
            tables = pd.read_html(io.StringIO(response.text), flavor=['lxml', 'html5lib'])
            
            df = format_kbo_table(tables[0])
            display_full_table(df) 
            
        except ValueError as e:
            if "No tables found" in str(e):
                st.warning("⚠️ 현재 KBO 홈페이지에서 해당 데이터를 텍스트 표로 제공하지 않고 있습니다.")
            else:
                st.error(f"데이터 해석 중 오류가 발생했습니다: {e}")
        except Exception as e:
            st.error(f"인터넷 연결 등 문제가 발생했습니다: {e}")

# ==========================================
# 6. 메뉴별 기능 매핑
# ==========================================
if menu == "🔍 선수 상세 기록실 (통합)":
    st.title("⚾ KBO 선수 상세 기록 검색 (타자/투수 통합)")
    st.markdown("선수 이름(예: 구자욱, 원태인, 류현진)을 입력하면 투수인지 타자인지 자동으로 파악하여 기록을 가져옵니다.")
    
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
                        player_link = player_links[0]['href']
                        detail_url = "https://www.koreabaseball.com" + player_link
                        
                        detail_response = requests.get(detail_url, headers=headers)
                        # ⭐ 수정됨: io.StringIO()를 사용하여 안전하게 텍스트 전달
                        tables = pd.read_html(io.StringIO(detail_response.text))
                        
                        player_stats = format_kbo_table(tables[0])
                        st.success(f"성공! {name} 선수의 기록입니다.")
                        
                        display_full_table(player_stats)
                        
                except ValueError:
                    st.warning("선수의 상세 기록 표를 불러오지 못했습니다.")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
        else:
            st.warning("선수 이름을 먼저 입력해주세요.")

elif menu == "🏆 정규시즌 팀 순위":
    fetch_and_display_data("🏆 정규시즌 팀 순위", "https://www.koreabaseball.com/TeamRank/TeamRank.aspx")

elif menu == "🏃 타자 순위 (Top 30)":
    fetch_and_display_data("🏃 타자 순위 (Top 30)", "https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx")

elif menu == "⚾ 투수 순위 (Top 30)":
    fetch_and_display_data("⚾ 투수 순위 (Top 30)", "https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx")

elif menu == "🏟️ 관중 현황":
    fetch_and_display_data("🏟️ 구단별 관중 현황", "https://www.koreabaseball.com/Record/Crowd/GraphDaily.aspx")

elif menu == "📜 역대 기록 (타자)":
    fetch_and_display_data("📜 역대 기록 (타자 부문)", "https://www.koreabaseball.com/Record/History/Top/Hitter.aspx")

elif menu == "📜 역대 기록 (투수)":
    fetch_and_display_data("📜 역대 기록 (투수 부문)", "https://www.koreabaseball.com/Record/History/Top/Pitcher.aspx")

elif menu == "🎯 예상 달성 기록":
    fetch_and_display_data("🎯 이번 시즌 예상 달성 기록", "https://www.koreabaseball.com/Record/Expectation/WeekView.aspx")
