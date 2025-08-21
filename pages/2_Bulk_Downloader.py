# pages/2_Bulk_Downloader.py
import os, io, zipfile, requests, streamlit as st

st.set_page_config(page_title="Bulk Downloader", layout="wide")
st.title("📦 Bulk Downloader (허용 소스만)")
st.caption("Pexels / Pixabay / Wikimedia / Openverse URL을 줄바꿈으로 붙여넣으면 ZIP으로 내려받습니다. (YouTube 제외)")

urls = st.text_area("다운로드 URL 목록", height=200, placeholder="한 줄에 하나씩 붙여넣기")
if st.button("ZIP 다운로드 만들기", use_container_width=True) and urls.strip():
    safe_domains = ("pexels.com","pixabay.com","wikimedia.org","upload.wikimedia.org","commons.wikimedia.org","openverse.org","staticflickr.com","flickr.com")
    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)

    n_ok, n_skip = 0, 0
    for raw in urls.splitlines():
        u = raw.strip()
        if not u: continue
        if not any(d in u for d in safe_domains):
            n_skip += 1
            continue
        try:
            r = requests.get(u, timeout=20)
            if r.ok and r.content:
                name = u.split("/")[-1] or f"file_{n_ok}.bin"
                zf.writestr(name, r.content)
                n_ok += 1
            else:
                n_skip += 1
        except Exception:
            n_skip += 1

    zf.close()
    st.success(f"완료: {n_ok}개 저장, {n_skip}개 건너뜀")
    st.download_button("ZIP 받기", data=buf.getvalue(), file_name="assets.zip", mime="application/zip")
else:
    st.info("주의: 각 라이선스 조건(표시, 개작 여부 등)을 영상 설명란에 표기하세요.")
