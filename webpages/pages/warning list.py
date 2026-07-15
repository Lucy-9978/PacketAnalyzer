import sqlite3

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide", page_title="네트워크 공격 탐지 대시보드")

# TODO: 실제 DB 접속 정보에 맞게 수정하세요.
# SQLite가 아니라 PostgreSQL(psycopg2)을 쓰는 경우 load_warnings()의
# connect/query 부분만 바꿔주면 나머지 로직은 그대로 사용할 수 있습니다.
DB_PATH = "warnings.db"

ATTACK_TYPES = [
    "ACK flood", "DNS Amplification", "Fin flood", "NULL Scan",
    "SSDP Amplification", "SYN flood", "SYN Scan", "FIN Scan",
    "RST flood", "UDP flood", "UDP Scan", "Xmas Scan",
]


def load_warnings() -> pd.DataFrame:
    """warnings 테이블에서 경고 목록을 읽어온다."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            """
            SELECT id, first_timestamp, last_timestamp, src_ip, attack_type, counter
            FROM warnings
            ORDER BY last_timestamp DESC
            """,
            conn,
        )
    finally:
        conn.close()
    return df


def grade_from_counter(counter: int) -> str:
    """발생 횟수(counter)를 기준으로 위험 등급을 계산한다.
    임계값은 팀 기준에 맞게 조정하세요."""
    if counter >= 200:
        return "Critical"
    elif counter >= 100:
        return "High"
    elif counter >= 50:
        return "Medium"
    elif counter >= 1:
        return "Low"
    return "None"


def make_detail_text(row: pd.Series) -> str:
    return (
        f"{row['attack_type']} 패턴 감지 - "
        f"최초 탐지 {row['first_timestamp']} / 최근 탐지 {row['last_timestamp']}, "
        f"누적 발생 {row['counter']}회"
    )


# --- 자동 새로고침 설정 ---
refresh_count = None
try:
    from streamlit_autorefresh import st_autorefresh
    refresh_count = st_autorefresh(interval=3000, key="data_refresh")
except ImportError:
    st.warning(
        "실시간 자동 새로고침을 사용하려면 터미널에서 "
        "`pip install streamlit-autorefresh` 를 실행하세요. "
        "(설치 전에는 페이지를 수동으로 새로고침해야 합니다.)"
    )

# --- 핵심 수정 포인트 ---
# 체크박스를 클릭하면 스크립트가 재실행되는데, 예전 코드는 재실행될 때마다
# 무조건 새 데이터를 추가해서 목록이 흔들리고 세부정보가 사라지는 문제가 있었다.
# st_autorefresh가 돌려주는 refresh_count가 "실제로 타이머가 울려서 재실행된 경우"에만
# 바뀌므로, 그때만 DB를 다시 읽어오고 체크박스 클릭으로 인한 재실행에서는
# 기존 데이터를 그대로 사용한다.
if "warnings_df" not in st.session_state:
    st.session_state.warnings_df = load_warnings()
    st.session_state.last_refresh_count = refresh_count

if refresh_count is not None and refresh_count != st.session_state.last_refresh_count:
    st.session_state.warnings_df = load_warnings()
    st.session_state.last_refresh_count = refresh_count

df = st.session_state.warnings_df

st.title("경고 목록")

# --- 공격 유형별 카운트 차트 ---
counts = df["attack_type"].value_counts().reindex(ATTACK_TYPES, fill_value=0)
chart_df = counts.reset_index()
chart_df.columns = ["Attack Type", "Attack Count"]

chart = (
    alt.Chart(chart_df)
    .mark_bar(size=22)
    .encode(
        x=alt.X("Attack Type", sort=ATTACK_TYPES, title=None,
                axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("Attack Count", title="Attack Count"),
        tooltip=["Attack Type", "Attack Count"],
    )
    .properties(height=350)
)
st.altair_chart(chart, use_container_width=True)

st.divider()

col_list, col_detail = st.columns([1.3, 1])

with col_list:
    st.subheader("Attack Packet List")

    display_rows = df.head(50).to_dict("records")

    header_cols = st.columns([0.6, 2, 2, 2, 1.3])
    for c, h in zip(header_cols, ["", "Timestamp", "Attack Type", "Src IP", "Attack Grade"]):
        c.markdown(f"**{h}**")

    with st.container(height=420):
        for row in display_rows:
            row_cols = st.columns([0.6, 2, 2, 2, 1.3])
            row_cols[0].checkbox("", key=f"chk_{row['id']}", label_visibility="collapsed")
            row_cols[1].write(row["last_timestamp"])
            row_cols[2].write(row["attack_type"])
            row_cols[3].write(row["src_ip"])
            row_cols[4].write(grade_from_counter(row["counter"]))

    selected_ids = [row["id"] for row in display_rows if st.session_state.get(f"chk_{row['id']}")]

with col_detail:
    st.subheader("Packet Detail Analysis")

    if not selected_ids:
        st.info("좌측 목록에서 항목을 체크하면 세부 데이터가 여기에 표시됩니다.")
    else:
        rows_by_id = {row["id"]: row for row in display_rows}
        selected_rows = [rows_by_id[rid] for rid in selected_ids if rid in rows_by_id]

        st.markdown("**Detail Data View**")
        detail_lines = [make_detail_text(pd.Series(row)) for row in selected_rows]
        st.text_area(
            "선택된 경고 상세",
            "\n".join(detail_lines),
            height=150,
            disabled=True,
            label_visibility="collapsed",
        )

        st.markdown("**등급 (Grade Selection)**")
        st.selectbox(
            "Grade Selection",
            ["Critical", "High", "Medium", "Low", "None"],
            key="grade_select",
            label_visibility="collapsed",
        )

        st.markdown("**차단**")
        st.toggle("차단 여부", key="block_toggle")

        st.markdown("**Analysis Notes**")
        st.text_area(
            "분석 메모", key="analysis_notes", height=120,
            label_visibility="collapsed",
        )

        st.caption(f"선택된 경고 수: {len(selected_rows)}개")