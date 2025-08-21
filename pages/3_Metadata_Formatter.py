# pages/3_Metadata_Formatter.py
import streamlit as st

st.set_page_config(page_title="Metadata Formatter", layout="wide")
st.title("📝 Metadata Formatter")
st.caption("저작자·라이선스·원본 링크를 입력하면 설명란에 붙일 표기문을 자동 생성합니다.")

col1, col2 = st.columns(2)
with col1:
    author  = st.text_input("저작자(Author)", placeholder="예: Jane Doe / 국회사진팀")
    license_ = st.text_input("라이선스(License)", placeholder="예: CC BY 4.0 / KOGL Type 1 / Pexels License")
with col2:
    source  = st.text_input("원본 링크(Source URL)", placeholder="https://commons.wikimedia.org/wiki/File:...")
    changes = st.text_input("변경 여부(선택)", placeholder="예: 색상 보정 / 크롭 / 자막 추가")

if st.button("표기문 만들기", use_container_width=True):
    line = f"{author} — {license_}. Source: {source}"
    if changes.strip():
        line += f" (Changes: {changes})"
    st.code(line, language="text")
    st.success("완료! 복사해서 영상 설명란에 넣으세요.")
else:
    st.info("Commons/CC/KOGL 등의 조건을 준수하세요. (예: CC BY는 저작자·라이선스·링크 표기 필수)")
