import bisect
import ipaddress
import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
IPV4_CSV_PATH = os.path.normpath(os.path.join(BASE_DIR,"ipv4.csv"))
COUNTRIES_CSV_PATH = os.path.normpath(os.path.join(BASE_DIR,"countries.csv"))


@st.cache_data
def load_index():
    """ipv4.csv, countries.csv를 불러와 이진 탐색용으로 정렬/인덱싱"""
    ipv4_df = pd.read_csv(IPV4_CSV_PATH)
    
    ipv4_df["start_int"] = ipv4_df["start_ip"].apply(lambda x: int(ipaddress.IPv4Address(x)))
    ipv4_df["end_int"] = ipv4_df["end_ip"].apply(lambda x: int(ipaddress.IPv4Address(x)))
    ipv4_df = ipv4_df.sort_values("start_int").reset_index(drop=True)

    start_list = ipv4_df["start_int"].tolist()
    end_list = ipv4_df["end_int"].tolist()
    country_list = ipv4_df["country_code"].tolist()

    countries_df = pd.read_csv(COUNTRIES_CSV_PATH)
    # 컬럼명 공백/대소문자 차이로 인한 KeyError 방지
    countries_df.columns = countries_df.columns.str.strip().str.lower()

    return start_list, end_list, country_list, countries_df


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str:
    """df.columns 중 candidates 후보군과 일치하는 컬럼명을 찾아 반환.
    못 찾으면 실제 컬럼 목록을 포함한 에러를 발생시킴."""
    for name in candidates:
        if name in df.columns:
            return name
    raise KeyError(
        f"{candidates} 중 일치하는 컬럼을 찾을 수 없습니다. "
        f"실제 컬럼: {df.columns.tolist()}"
    )


def get_ip_location(ip: str):
    """IP를 받아 (국가코드, 위도, 경도)를 반환. 못 찾으면 None."""
    start_list, end_list, country_list, countries_df = load_index()

    try:
        target_ip_int = int(ipaddress.IPv4Address(ip))
    except ValueError:
        return None

    idx = bisect.bisect_right(start_list, target_ip_int) - 1
    if idx < 0 or not (start_list[idx] <= target_ip_int <= end_list[idx]):
        return None

    country_code = country_list[idx]

    iso_col = _find_column(countries_df, ["iso", "iso2", "iso_a2", "country_code", "code"])
    lat_col = _find_column(countries_df, ["latitude", "lat"])
    lon_col = _find_column(countries_df, ["longitude", "lon", "lng"])

    matched = countries_df[countries_df[iso_col] == country_code]
    if matched.empty:
        return None

    latitude = matched.iloc[0][lat_col]
    longitude = matched.iloc[0][lon_col]
    return country_code, latitude, longitude


# ---------------- Streamlit UI ----------------
st.title("IP 국가 위치 조회")



target_ip = st.text_input("조회할 IP를 입력하세요", value="14.102.130.5")

if st.button("조회"):
    result = get_ip_location(target_ip)

    if result is None:
        st.error(f"'{target_ip}'에 대한 국가/위치 정보를 찾을 수 없습니다.")
    else:
        country_code, latitude, longitude = result
        st.success(f"IP: {target_ip} -> 국가코드(ISO): {country_code}")
        st.write(f"위도: {latitude}, 경도: {longitude}")

        map_df = pd.DataFrame({"lat": [latitude], "lon": [longitude]})
        st.map(map_df, zoom=3)