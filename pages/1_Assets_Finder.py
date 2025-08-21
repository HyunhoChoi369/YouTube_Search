# pages/1_Assets_Finder.py
import datetime as dt
import streamlit as st
from lib import config, providers, utils

st.set_page_config(page_title="Assets Finder", layout="wide")
st.title("📚 Assets Finder")
config.render_key_inputs()

with st.sidebar:
    st.header("⚙️ 검색 옵션")
    query = st.text_input("검색어(이슈/인물/장면)", placeholder="예: 국회 본회의, 윤석열, US debate, protest crowd")
    media_types = st.multiselect("타입", ["photo","video"], default=["photo","video"])
    is_person   = st.checkbox("인물(P18) 우선", value=True)
    max_results = st.slider("최대 결과/소스", 5, 50, 20, step=5)
    want_vertical = st.checkbox("세로(9:16) 우선", value=True)
    safe_search = st.checkbox("세이프서치(가능한 소스만)", value=True)
    cc_only_openverse = st.selectbox("Openverse 라이선스", ["any","cc0","by","by-sa","by-nc","by-nd","by-nc-sa","by-nc-nd"], index=0)
    use_sources = st.multiselect("사용 소스", ["Wikidata/Commons(P18)","Pexels","Pixabay","Openverse","YouTube(CC-BY 메타만)"],
                                 default=["Wikidata/Commons(P18)","Pexels","Pixabay","Openverse","YouTube(CC-BY 메타만)"])

if st.button("검색 실행", use_container_width=True) and query.strip():
    items = []

    # P18 (인물)
    if is_person and "Wikidata/Commons(P18)" in use_sources:
        wd = providers.wikidata_p18_image(query)
        if wd: items.append(wd)

    # Pexels
    if "Pexels" in use_sources and (set(media_types) & {"photo","video"}):
        items += providers.search_pexels(
            config.get("PEXELS_KEY"), query, per_page=max_results,
            want_video=("video" in media_types), orientation=("portrait" if want_vertical else None)
        )

    # Pixabay
    if "Pixabay" in use_sources and (set(media_types) & {"photo","video"}):
        items += providers.search_pixabay(
            config.get("PIXABAY_KEY"), query, per_page=max_results,
            want_video=("video" in media_types), safesearch=safe_search
        )

    # Openverse (photos)
    if "Openverse" in use_sources and "photo" in media_types:
        items += providers.search_openverse(query, per_page=max_results, license_type=cc_only_openverse)

    # YouTube (CC-BY 메타만, 링크 제공)
    if "YouTube(CC-BY 메타만)" in use_sources and "video" in media_types:
        items += providers.search_youtube_cc(config.get("YOUTUBE_API_KEY"), query, per_page=max_results)

    # 점수/정렬/중복 제거
    for it in items:
        it["score"] = utils.compute_score(it, prefer_vertical=want_vertical)
    items = utils.dedup_items(items)
    items.sort(key=lambda x: x["score"], reverse=True)

    st.write(f"총 {len(items)}개 결과")
    cols = st.columns(3)
    picks = []
    for i, it in enumerate(items):
        with cols[i % 3]:
            st.markdown(f"**{it['provider']} · {it['type']}**  \nScore: {it['score']:.2f}")
            st.image(it["preview"], use_column_width=True)
            st.markdown(utils.license_block(it))
            if st.checkbox("선택", key=f"pick_{i}"):
                picks.append(it)

    if picks:
        st.subheader("✅ 선택한 항목")
        st.download_button(
            "메타데이터 CSV 내보내기",
            data=utils.csv_from_items(picks),
            file_name=f"assets_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        st.info("📥 Pexels/Pixabay/Wikimedia/Openverse는 다운로드 사용 가능(각 라이선스 준수). YouTube는 링크만 사용하세요.")
else:
    st.info("좌측 옵션을 설정하고 ‘검색 실행’을 눌러보세요.")
