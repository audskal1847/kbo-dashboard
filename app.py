import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

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
    
    # 데이터가 제대로 제공되지 않는 '팀 순위'와 '예상 달성 기록' 삭제
    menu = st.radio(
        "원하시는 항목을 선택하세요:",
        [
            "🔍 선수 상세 기록실 (통합)", 
            "🏃 타자 순위 (Top 30)", 
            "⚾ 투수 순위 (Top 30)", 
            "🏟️ 관중 현황",
            "📜 역대 기록 (타자)",
            "📜 역대 기록 (투수)",
            "⚔️ 스탯티즈 만능 데이터 검색"
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
# 4. 공통 크롤링 실행 함수 
# ==========================================
def fetch_and_display_data(title, url, loading_msg="데이터를 불러오는 중입니다..."):
    st.title(title)
    with st.spinner(loading_msg):
        try:
            response = requests.get(url, headers=headers)
            tables = pd.read_html(io.StringIO(response.text), flavor=['lxml', 'html5lib'])
            
            df = format_kbo_table(tables[0])
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
                        tables = pd.read_html(io.StringIO(detail_response.text))
                        
                        player_stats = format_kbo_table(tables[0])
                        st.success(f"성공! {name} 선수의 기록입니다.")
                        
                        st.dataframe(player_stats, use_container_width=True, hide_index=True)
                        
                except ValueError:
                    st.warning("선수의 상세 기록 표를 불러오지 못했습니다.")
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

elif menu == "📜 역대 기록 (타자)":
    fetch_and_display_data("📜 역대 기록 (타자 부문)", "https://www.koreabaseball.com/Record/History/Top/Hitter.aspx")

elif menu == "📜 역대 기록 (투수)":
    fetch_and_display_data("📜 역대 기록 (투수 부문)", "https://www.koreabaseball.com/Record/History/Top/Pitcher.aspx")

# ==========================================
# 6. 스탯티즈 만능 크롤러
# ==========================================
elif menu == "⚔️ 스탯티즈 만능 데이터 검색":
    st.title("⚔️ 스탯티즈 만능 데이터 검색")
    st.markdown("원하시는 스탯티즈(Statiz) 페이지의 인터넷 주소(URL)를 복사해서 아래 빈칸에 붙여넣어주세요. 해당 페이지에 있는 모든 통산 성적과 대결 기록 표를 한 번에 긁어옵니다!")
    
    default_statiz_url = "https://statiz.co.kr/team/?m=cteam&ct_code=1"
    statiz_url = st.text_input("🔗 스탯티즈 주소(URL) 입력:", value=default_statiz_url)

    if st.button("스탯티즈 데이터 가져오기", type="primary"):
        with st.spinner("스탯티즈에서 통산 기록과 대결 기록을 수집하는 중입니다..."):
            try:
                response = requests.get(statiz_url, headers=headers)
                tables = pd.read_html(io.StringIO(response.text), flavor=['lxml', 'html5lib'])
                
                if not tables:
                    st.warning("입력하신 페이지에는 표 형태의 데이터가 없습니다.")
                else:
                    st.success(f"성공! 총 {len(tables)}개의 표를 찾았습니다.")
                    for i, table in enumerate(tables):
                        st.subheader(f"📊 수집된 데이터 표 {i+1}")
                        table.dropna(how='all', inplace=True)
                        st.dataframe(table, use_container_width=True, hide_index=True)
                        
            except ValueError:
                st.error("해당 주소에서 읽을 수 있는 표 구조를 찾지 못했습니다. 주소를 다시 확인해주세요.")
            except Exception as e:
                st.error(f"오류가 발생했습니다 (서버 보안에 막혔을 수 있습니다): {e}")
