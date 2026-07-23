from engine import PacketData, Flow

PORT_THRESHOLD = 10
PPS_THRESHOLD = 20


def detect(packet: PacketData, flow: Flow):

    # TCP가 아니면 검사하지 않음
    if flow.protocol != "TCP":
        return (False, "")

    # Xmas Scan 패킷만 검사 (FIN+PSH+URG가 동시에 켜진 패킷)
    if packet.tcp_flags != "FPU":
        return (False, "")

    # 최근 50개 패킷 기준으로 해당 출발지 IP가 접근한 목적지 포트
    unique_ports = flow.get_dst_unique_ports(10, packet.src_ip)

    # SYN/FIN 탐지기가 flow.syn_count / flow.fin_count를 쓰는 것과 동일하게,
    # Xmas 패킷 누적 카운트도 flow.xmas_count로 관리한다고 가정.
    scan_type = "Xmas"
    scan_count = flow.xmas_count

    # Scan 탐지
    if (
        len(unique_ports) >= PORT_THRESHOLD
        and scan_count >= PORT_THRESHOLD
        and flow.pps >= PPS_THRESHOLD
    ):

        print(
            f"[{scan_type} Scan Detected]",
            f"src={packet.src_ip}",
            f"ports={sorted(unique_ports)}",
            f"xmas={scan_count}",
            f"pps={flow.pps:.2f}"
        )
        return (True, f"{scan_type} Scan")
    return (False, "")