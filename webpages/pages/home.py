import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Packet Analyzer",
    layout="wide"
)

conn = sqlite3.connect("packets.db")

st.title("🛡 Packet Analyzer")

########################################################
# 최근 60초 데이터
########################################################

now = int(datetime.now().timestamp())
start = now - 60

packets = pd.read_sql_query("""
SELECT *
FROM packets
WHERE timestamp >= ?
""", conn, params=(start,))

warnings = pd.read_sql_query("""
SELECT *
FROM warnings
ORDER BY last_timestamp DESC
LIMIT 10
""", conn)

########################################################
# KPI
########################################################

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Packets",
        len(packets)
    )

with col2:
    st.metric(
        "PPS",
        round(len(packets)/60, 1)
    )

with col3:
    st.metric(
        "Warnings",
        len(warnings)
    )

with col4:
    st.metric(
        "Active Source IP",
        packets["src_ip"].nunique()
    )

st.divider()

traffic = (
    packets.groupby("timestamp")
    .size()
    .reset_index(name="Packets")
)

fig = px.line(
    traffic,
    x="timestamp",
    y="Packets",
    markers=True
)

fig.update_layout(
    xaxis_title="Time",
    yaxis_title="Packets/sec",
    height=350
)

st.plotly_chart(fig, width='stretch')

left, right = st.columns(2)
with left:

    st.subheader("Protocol Distribution")

    proto = (
        packets["protocol"]
        .value_counts()
        .reset_index()
    )

    proto.columns = ["Protocol", "Count"]

    fig = px.pie(
        proto,
        names="Protocol",
        values="Count"
    )

    st.plotly_chart(fig, width='stretch')

with right:

    st.subheader("Recent Alerts")

    if warnings.empty:
        st.success("No Warning")

    else:

        for _, row in warnings.iterrows():

            st.error(
                f"""
{row.attack_type}

IP : {row.src_ip}
Count : {row.counter}
"""
            )

left, right = st.columns(2)
with left:

    st.subheader("Top Source IP")

    top = (
        packets.groupby("src_ip")
        .size()
        .sort_values(ascending=False)
        .head(10)
    )

    st.dataframe(top)
with right:

    st.subheader("Recent Packets")

    recent = packets.sort_values(
        "timestamp",
        ascending=False
    ).head(10)

    st.dataframe(
        recent[
            [
                "timestamp",
                "src_ip",
                "dst_ip",
                "protocol",
                "packet_size"
            ]
        ],
        width='stretch'
    )