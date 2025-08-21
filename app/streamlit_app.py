# app.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from lib import config, providers, utils


st.set_page_config(page_title="Shorts Asset Toolkit", layout="wide")
st.title("🎬 Shorts Asset Toolkit")
st.caption("정치·시사 쇼츠 제작을 위한 자료 수집/정리 도구 모음")

config.render_key_inputs()

st.markdown("""
### 무엇을 할 수 있나요?
- **Assets Finder**: 키워드/인물명으로 사진·영상 후보를 모아서 **라이선스/출처**와 함께 보여줘요.
- **Bulk Downloader**: Pexels/Pixabay/Commons/Openverse처럼 **다운로드 허용**되는 소스만 한 번에 저장해요.
- **Metadata Formatter**: 파일별 **저작자·라이선스·원본 링크**를 자동 문장으로 만들어 설명란에 복붙!

> 좌측 사이드바에서 API 키를 입력해두면 모든 페이지에서 공유됩니다.
""")
