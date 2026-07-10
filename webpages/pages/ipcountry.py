import bisect
import ipaddress
import pandas as pd

# 이후에 packets.db의 packets나 warnings 테이블에서 src_ip들고 오면됨
target_ip = "14.102.130.5"


ipv4_df = pd.read_csv("ipv4.csv")
ipv4_df.columns = ["base_date", "country_code", "start_ip", "end_ip", "prefix", "assigned_date"]


countries_df = pd.read_csv("countries.csv")

# 3. 인덱싱: IP를 정수로 변환하고 start_ip 기준 정렬
ipv4_df["start_int"] = ipv4_df["start_ip"].apply(lambda x: int(ipaddress.IPv4Address(x)))
ipv4_df["end_int"] = ipv4_df["end_ip"].apply(lambda x: int(ipaddress.IPv4Address(x)))
ipv4_df = ipv4_df.sort_values("start_int").reset_index(drop=True)

start_list = ipv4_df["start_int"].tolist()   # 이진 탐색용 정렬된 리스트
end_list = ipv4_df["end_int"].tolist()
country_list = ipv4_df["country_code"].tolist()

# 4. 이진 탐색으로 target_ip가 속한 대역 찾기
target_ip_int = int(ipaddress.IPv4Address(target_ip))

idx = bisect.bisect_right(start_list, target_ip_int) - 1  # start_ip <= target_ip 인 마지막 위치

found_country_code = None
if idx >= 0 and start_list[idx] <= target_ip_int <= end_list[idx]:
    found_country_code = country_list[idx]

# 5. 찾은 국가코드로 countries.csv 에서 위도/경도 조회
if found_country_code is not None:
    matched = countries_df[countries_df["ISO"] == found_country_code]
    if not matched.empty:
        latitude = matched.iloc[0]["latitude"]
        longitude = matched.iloc[0]["longitude"]
        print(f"IP: {target_ip}")
        print(f"국가코드(ISO): {found_country_code}")
        print(f"위도: {latitude}")
        print(f"경도: {longitude}")
    else:
        print(f"국가코드 '{found_country_code}'에 대한 위경도 정보를 countries.csv에서 찾을 수 없습니다.")
else:
    print(f"IP '{target_ip}'에 해당하는 국가 대역을 ipv4.csv에서 찾을 수 없습니다.")