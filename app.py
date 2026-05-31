import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="도윤이의 KBO 기록 검색기", page_icon="⚾", layout="wide")

# ==========================================
# ⭐ 배경 사진 투명도(0.95) 및 전체 글씨 굵게(Bold) 적용
# ==========================================
background_image_url = "https://github.com/audskal1847/kbo-dashboard/blob/main/KakaoTalk_20260531_064807857.png?raw=true"

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)), url("{background_image_url}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}

/* 화면의 모든 주요 글자를 진하게 만듭니다 */
p, span, label, h1, h2, h3, h4, h5, h6, th, td {{
    font-weight: 700 !important;
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
    sidebar_image_url = "https://github.com/audskal1847/kbo-dashboard/blob/main/KakaoTalk_20260531_064816799.jpg?raw=true"
    
    st.image(sidebar_image_url, width=150)
    st.markdown("---")
    
    st.header("📊 데이터 메뉴")
    
    menu = st.radio(
        "원하시는 항목을 선택하세요:",
        [
            "🔍 1. 도윤이의 선수 검색기", 
            "🏟️ 2. 구단 소개",
            "🏆 3. 정규시즌 팀 순위", 
            "🏃 4. 타자 순위 (Top 30)", 
            "⚾ 5. 투수 순위 (Top 30)", 
            "🏟️ 6. 관중 현황",
            "📊 7. 팀 간 상대전적 (엑셀)", 
            "📅 8. 연도별 종합성적 (엑셀)", 
            "🏅 9. 역대 통산성적 (엑셀)",  
            "📜 10. 역대 기록 (구단)", 
            "📜 11. 역대 기록 (타자)",
            "📜 12. 역대 기록 (투수)"
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
# ⭐ 5. 깃허브에 내장된 엑셀 파일을 읽어오는 함수 (초고속!)
# ==========================================
def display_local_excel(title, file_name):
    st.title(title)
    st.markdown(f"깃허브에 내장된 **[{file_name}]** 파일에서 데이터를 불러왔습니다.")
    
    try:
        # 업로드 창 없이, 깃허브에 있는 파일을 즉시 읽어 들입니다.
        xls = pd.ExcelFile(file_name)
        sheet_names = xls.sheet_names
        
        # 시트가 여러 개일 경우 팀을 선택할 수 있게 합니다.
        if len(sheet_names) > 1:
            selected_sheet = st.selectbox("기록을 확인할 시트(팀)를 선택하세요:", sheet_names)
            df = pd.read_excel(file_name, sheet_name=selected_sheet)
            st.subheader(f"📂 {selected_sheet} 데이터")
        else:
            df = pd.read_excel(file_name)
            
        st.dataframe(df, use_container_width=True)
        
    except FileNotFoundError:
        st.error(f"⚠️ '{file_name}' 파일을 찾을 수 없습니다! 깃허브에 파일이 정확한 이름으로 업로드되었는지 확인해주세요.")
    except Exception as e:
        st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")

# ==========================================
# 6. 메뉴별 기능 매핑 
# ==========================================
if menu == "🔍 1. 도윤이의 선수 검색기":
    st.title("⚾ 도윤이의 KBO 기록 검색기") 
    st.markdown("선수 이름(예: 원태인, 구자욱)을 입력하면 선수들의 기록을 찾아서 보여줍니다.")
    
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
                        
                        valid_results = []
                        
                        for href in unique_links:
                            detail_url = "https://www.koreabaseball.com" + href
                            detail_response = requests.get(detail_url, headers=headers)
                            tables = pd.read_html(io.StringIO(detail_response.text))
                            
                            player_stats = format_kbo_table(tables[0])
                            
                            if player_stats.empty:
                                continue
                            if len(player_stats) > 0 and "기록이 없습니다" in str(player_stats.iloc[0].values):
                                continue
                                
                            team_name = ""
                            if '팀명' in player_stats.columns:
                                teams = player_stats['팀명'].dropna().astype(str)
                                teams = teams[~teams.str.contains('기록이 없습니다|통산|합계', na=False)]
                                if not teams.empty:
                                    team_name = teams.iloc[-1]
                                player_stats = player_stats.drop(columns=['팀명'])
                            
                            if '평균자책' in player_stats.columns or '평균자책점' in player_stats.columns:
                                position = "투수"
                            else:
                                position = "야수"
                            
                            if team_name:
                                team_pos_str = f"({team_name}, {position})"
                            else:
                                team_pos_str = f"({position})"
                            
                            valid_results.append((team_pos_str, player_stats))
                        
                        if valid_results:
                            st.success(f"성공! 총 {len(valid_results)}명의 1군 기록이 있는 '{name}' 선수를 찾았습니다.")
                            for team_pos_str, stats in valid_results:
                                st.markdown(f"#### 👤 {name} 선수 {team_pos_str}")
                                st.dataframe(stats, use_container_width=True, hide_index=True)
                                st.markdown("---")
                        else:
                            st.warning(f"'{name}' 선수의 1군 기록을 찾을 수 없습니다. (신인 또는 기록 없음)")
                        
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
        else:
            st.warning("선수 이름을 먼저 입력해주세요.")

elif menu == "🏟️ 2. 구단 소개":
    st.title("🏟️ KBO 리그 구단 소개")
    with st.spinner("구단 정보를 불러오는 중입니다..."):
        try:
            url = "https://www.koreabaseball.com/Kbo/League/TeamInfo.aspx"
            response = requests.get(url, headers=headers)
            tables = pd.read_html(io.StringIO(response.text), flavor=['lxml', 'html5lib'])
            
            if tables:
                df = tables[0]
                cols_to_drop = [col for col in df.columns if 'Unnamed' in str(col)]
                df.drop(columns=cols_to_drop, inplace=True)
                df.dropna(how='all', inplace=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("데이터를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")

elif menu == "🏆 3. 정규시즌 팀 순위":
    st.title("🏆 정규시즌 팀 순위")
    st.markdown("현재 KBO 리그 팀 순위입니다. (가장 빠르고 정확한 KBO 공식 실시간 데이터를 가져옵니다)")
    
    with st.spinner("순위 데이터를 불러오는 중입니다..."):
        try:
            kbo_url = "https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx"
            response = requests.get(kbo_url, headers=headers)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'tData'})
            
            if table:
                df = pd.read_html(io.StringIO(str(table)))[0]
                
                for col in df.columns:
                    if 'Unnamed' in str(col):
                        df.rename(columns={col: '순위'}, inplace=True)
                
                if '승률' in df.columns:
                    df['승률'] = pd.to_numeric(df['승률'], errors='coerce').map('{:.3f}'.format)
                
                if '게임차' in df.columns:
                    df['게임차'] = pd.to_numeric(df['게임차'], errors='coerce').map('{:.1f}'.format)
                
                st.success("성공! KBO 공식 홈페이지의 실시간 팀 순위입니다.")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("현재 KBO 홈페이지에서 팀 순위 표를 제공하지 않고 있습니다.")
                
        except Exception as e:
            st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")

elif menu == "🏃 4. 타자 순위 (Top 30)":
    fetch_and_display_data("🏃 타자 순위 (Top 30)", "https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx")

elif menu == "⚾ 5. 투수 순위 (Top 30)":
    fetch_and_display_data("⚾ 투수 순위 (Top 30)", "https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx")

elif menu == "🏟️ 6. 관중 현황":
    fetch_and_display_data("🏟️ 구단별 관중 현황", "https://www.koreabaseball.com/Record/Crowd/GraphDaily.aspx")

# ⭐ 버튼 하나 누르면 내장된 파일을 즉시 불러오는 엑셀 메뉴!
elif menu == "📊 7. 팀 간 상대전적 (엑셀)":
    display_local_excel("📊 팀 간 상대전적", "팀 간 상대전적.xlsx")

elif menu == "📅 8. 연도별 종합성적 (엑셀)":
    display_local_excel("📅 연도별 종합성적", "연도별 종합성적.xlsx")

elif menu == "🏅 9. 역대 통산성적 (엑셀)":
    display_local_excel("🏅 역대 통산성적", "통산성적.xlsx")

elif menu == "📜 10. 역대 기록 (구단)":
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

elif menu == "📜 11. 역대 기록 (타자)":
    fetch_and_display_data("📜 역대 기록 (타자 부문)", "https://www.koreabaseball.com/Record/History/Top/Hitter.aspx")

elif menu == "📜 12. 역대 기록 (투수)":
    fetch_and_display_data("📜 역대 기록 (투수 부문)", "https://www.koreabaseball.com/Record/History/Top/Pitcher.aspx")
