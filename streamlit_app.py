import os, io, math, asyncio, datetime as dt
import requests
import streamlit as st
from urllib.parse import urlencode, quote

# -------------------------
# 기본 설정
# -------------------------
st.set_page_config(page_title="Shorts Asset Finder", layout="wide")

st.title("🎬 Shorts Asset Finder")
st.caption("정치·시사 이슈용 사진/영상 자동 수집 (라이선스·출처 자동기록)")

# 사이드바: API 키/옵션
with st.sidebar:
    st.header("🔐 API Keys (st.secrets 권장)")
    PEXELS_KEY   = st.text_input("Pexels API Key",  value=st.secrets.get("PEXELS_KEY", ""), type="password")
    PIXABAY_KEY  = st.text_input("Pixabay API Key", value=st.secrets.get("PIXABAY_KEY", ""), type="password")
    YT_KEY       = st.text_input("YouTube Data API Key (선택)", value=st.secrets.get("YOUTUBE_API_KEY", ""), type="password")

    st.header("⚙️ 검색 옵션")
    query = st.text_input("검색어(이슈/인물/장면)", placeholder="예: 국회 본회의, 윤석열, 미 대선 토론, protest crowd")
    media_types = st.multiselect("타입", ["photo","video"], default=["photo","video"])
    is_person   = st.checkbox("인물(정치인) P18 우선 탐색", value=True)
    max_results = st.slider("최대 결과/소스", 5, 50, 20, step=5)
    want_vertical = st.checkbox("세로(9:16) 우선", value=True)
    safe_search = st.checkbox("세이프서치(가능한 소스만)", value=True)
    cc_only_openverse = st.selectbox("Openverse 라이선스", ["any","cc0","by","by-sa","by-nc","by-nd","by-nc-sa","by-nc-nd"], index=0)
    use_sources = st.multiselect("사용 소스", ["Wikidata/Commons(P18)","Pexels","Pixabay","Openverse","YouTube(CC-BY 메타만)"],
                                 default=["Wikidata/Commons(P18)","Pexels","Pixabay","Openverse","YouTube(CC-BY 메타만)"])

def aspect_score(w,h, prefer_vertical=True):
    if not w or not h: return 0
    r = w / h
    target = 9/16 if prefer_vertical else 16/9
    return 1 - min(1, abs(r - target) / target)

def license_block(item):
    return f"**License**: {item.get('license','?')}  \n**Attribution**: {item.get('attribution','')}  \n**Source**: {item.get('source_url','')}"

# -------------------------
# 각 소스별 검색 함수
# -------------------------
def search_pexels(q, per_page=20, orientation=None):
    if not PEXELS_KEY: return []
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_KEY}
    params = {"query": q, "per_page": per_page}
    if orientation: params["orientation"] = orientation
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    out=[]
    for p in r.json().get("photos", []):
        out.append({
            "provider":"pexels","type":"photo",
            "preview": p["src"]["medium"], "download": p["src"]["original"],
            "width": p.get("width"), "height": p.get("height"),
            "license": "Pexels License",
            "attribution": f'{p.get("photographer","")} (Pexels)',
            "source_url": p.get("url")
        })
    # 비디오도 원하면 비디오 API
    if "video" in media_types:
        vr = requests.get("https://api.pexels.com/videos/search", headers=headers,
                          params={"query": q, "per_page": per_page}, timeout=20)
        if vr.ok:
            for v in vr.json().get("videos", []):
                files = v.get("video_files", [])
                best = max(files, key=lambda f: f.get("width",0)*f.get("height",0)) if files else {}
                out.append({
                    "provider":"pexels","type":"video",
                    "preview": v.get("image"), "download": best.get("link"),
                    "width": best.get("width"), "height": best.get("height"),
                    "duration": v.get("duration"),
                    "license": "Pexels License",
                    "attribution": f'Pexels Video by {v.get("user",{}).get("name","")}',
                    "source_url": v.get("url")
                })
    return out

def search_pixabay(q, per_page=20, safesearch=True):
    if not PIXABAY_KEY: return []
    base = "https://pixabay.com/api/"
    par = {"key": PIXABAY_KEY, "q": q, "per_page": per_page, "safesearch": str(safesearch).lower()}
    r = requests.get(base, params=par, timeout=20)
    out=[]
    if r.ok:
        for h in r.json().get("hits",[]):
            out.append({
                "provider":"pixabay","type":"photo",
                "preview": h.get("previewURL"), "download": h.get("largeImageURL"),
                "width": h.get("imageWidth"), "height": h.get("imageHeight"),
                "license": "Pixabay Content License",
                "attribution": f'{h.get("user","")} (Pixabay)',
                "source_url": h.get("pageURL")
            })
    if "video" in media_types:
        vr = requests.get("https://pixabay.com/api/videos/", params=par, timeout=20)
        if vr.ok:
            for h in vr.json().get("hits",[]):
                vids = h.get("videos",{})
                best = vids.get("large") or vids.get("medium") or vids.get("small") or {}
                out.append({
                    "provider":"pixabay","type":"video",
                    "preview": h.get("picture_id") and f"https://i.vimeocdn.com/video/{h['picture_id']}_640x360.jpg",
                    "download": best.get("url"),
                    "width": best.get("width"), "height": best.get("height"),
                    "duration": h.get("duration"),
                    "license": "Pixabay Content License",
                    "attribution": f'{h.get("user","")} (Pixabay)',
                    "source_url": h.get("pageURL")
                })
    return out

def search_openverse(q, per_page=20, license_type="any"):
    url = "https://api.openverse.org/v1/images/"
    params = {"q": q, "page_size": per_page}
    if license_type != "any":
        params["license_type"] = license_type
    r = requests.get(url, params=params, timeout=20)
    out=[]
    if r.ok:
        for rj in r.json().get("results",[]):
            out.append({
                "provider":"openverse","type":"photo",
                "preview": rj.get("thumbnail"), "download": rj.get("url"),
                "width": rj.get("width"), "height": rj.get("height"),
                "license": rj.get("license", "").upper(),
                "attribution": rj.get("attribution","Openverse"),
                "source_url": rj.get("foreign_landing_url") or rj.get("url")
            })
    return out

def wikidata_p18_image(name):
    """이름으로 위키데이터 검색→P18 파일→Commons 원본/라이선스 메타"""
    # 1) 엔터티 검색
    s = requests.get("https://www.wikidata.org/w/api.php",
                     params={"action":"wbsearchentities","search":name,"language":"ko","format":"json","limit":1}, timeout=20)
    if not s.ok or not s.json().get("search"): return None
    qid = s.json()["search"][0]["id"]
    # 2) 엔터티 상세
    e = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json", timeout=20)
    ent = e.json()["entities"][qid]
    claims = ent.get("claims",{})
    if "P18" not in claims: return None
    filename = claims["P18"][0]["mainsnak"]["datavalue"]["value"]  # e.g., "Yoon Suk-yeol in 2022.jpg"
    # 3) Commons 메타
    title = f"File:{filename}"
    c = requests.get("https://commons.wikimedia.org/w/api.php",
                     params={"action":"query","prop":"imageinfo","iiprop":"url|extmetadata","titles":title,"format":"json"}, timeout=20)
    pages = c.json().get("query",{}).get("pages",{})
    if not pages: return None
    page = next(iter(pages.values()))
    ii = (page.get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata",{})
    return {
        "provider":"wikimedia","type":"photo",
        "preview": ii.get("url"), "download": ii.get("url"),
        "width": None, "height": None,
        "license": meta.get("LicenseShortName",{}).get("value",""),
        "attribution": meta.get("Artist",{}).get("value","").strip() or "Wikimedia Commons",
        "source_url": f"https://commons.wikimedia.org/wiki/{title}"
    }

def search_youtube_cc(q, per_page=20):
    if not YT_KEY: return []
    params = {
        "part":"snippet","q":q,"type":"video","maxResults":min(per_page, 50),
        "videoLicense":"creativeCommon","safeSearch":"moderate"
    }
    r = requests.get("https://www.googleapis.com/youtube/v3/search", params={**params,"key":YT_KEY}, timeout=20)
    out=[]
    if r.ok:
        for item in r.json().get("items",[]):
            vid = item["id"]["videoId"]
            url = f"https://www.youtube.com/watch?v={vid}"
            thumb = item["snippet"]["thumbnails"]["medium"]["url"]
            out.append({
                "provider":"youtube","type":"video",
                "preview": thumb, "download": None,  # YouTube는 다운로드 금지(링크만)
                "width": None, "height": None,
                "license": "CC-BY (YouTube setting)",  # 실제 CC-BY 고지
                "attribution": item["snippet"].get("channelTitle","YouTube"),
                "source_url": url
            })
    return out

# -------------------------
# 실행
# -------------------------
if st.button("검색 실행", use_container_width=True) and query.strip():
    items = []

    # 위키데이터/커먼즈(P18): 인물 사진
    if is_person and "Wikidata/Commons(P18)" in use_sources:
        wd = wikidata_p18_image(query)
        if wd: items.append(wd)

    # Pexels
    if "Pexels" in use_sources and ("photo" in media_types or "video" in media_types):
        items += search_pexels(query, per_page=max_results, orientation="portrait" if want_vertical else None)

    # Pixabay
    if "Pixabay" in use_sources and ("photo" in media_types or "video" in media_types):
        items += search_pixabay(query, per_page=max_results, safesearch=safe_search)

    # Openverse
    if "Openverse" in use_sources and "photo" in media_types:
        items += search_openverse(query, per_page=max_results, license_type=cc_only_openverse)

    # YouTube (CC-BY 메타만, 링크 제공)
    if "YouTube(CC-BY 메타만)" in use_sources and "video" in media_types:
        items += search_youtube_cc(query, per_page=max_results)

    # 점수(세로우선 + 신뢰도 간단 가중)
    for it in items:
        it["score"] = 0.6*aspect_score(it.get("width"), it.get("height"), prefer_vertical=want_vertical) + \
                      0.4*(1 if it["provider"] in ["wikimedia","openverse","pexels","pixabay"] else 0.7)

    # 중복 제거(소스 URL 기준)
    dedup = {}
    for it in items:
        k = (it["provider"], it.get("source_url") or it.get("download") or it.get("preview"))
        if k not in dedup: dedup[k] = it
    items = sorted(dedup.values(), key=lambda x: x["score"], reverse=True)

    st.write(f"총 {len(items)}개 결과")
    cols = st.columns(3)
    picks = []
    for i, it in enumerate(items):
        with cols[i%3]:
            st.markdown(f"**{it['provider']} · {it['type']}**  \nScore: {it['score']:.2f}")
            if it["type"]=="photo":
                st.image(it["preview"], use_column_width=True)
            else:
                st.image(it["preview"], use_column_width=True)  # 썸네일
            st.markdown(license_block(it))
            ck = st.checkbox("선택", key=f"pick_{i}")
            if ck:
                picks.append(it)

    if picks:
        st.subheader("✅ 선택한 항목")
        st.download_button("메타데이터 CSV 내보내기",
                           data="provider,type,preview,download,width,height,duration,license,attribution,source_url\n" +
                                "\n".join([",".join([str(it.get(k,"")).replace(","," ") for k in
                                 ["provider","type","preview","download","width","height","duration","license","attribution","source_url"]]) for it in picks]),
                           file_name=f"assets_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           mime="text/csv")
        # 허용 소스만 직접 다운로드 안내
        st.info("📥 Pexels/Pixabay/Wikimedia/Openverse는 다운로드 사용 가능(각 라이선스 조건 준수). YouTube는 링크만 사용하세요.")
else:
    st.info("좌측에서 키/옵션을 설정하고 ‘검색 실행’을 눌러보세요!")
