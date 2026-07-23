from engine import PacketData, Flow

PORT_THRESHOLD = 10
PPS_THRESHOLD = 20


def detect(packet: PacketData, flow: Flow):

    # TCP가 아니면 검사하지 않음
    if flow.protocol != "TCP":
        return (False, "")

    # NULL Scan 패킷만 검사 (아무 플래그도 켜지지 않은 패킷)
    if packet.tcp_flags not in ("", None):
        return (False, "")

    # 최근 50개 패킷 기준으로 해당 출발지 IP가 접근한 목적지 포트
    unique_ports = flow.get_dst_unique_ports(10, packet.src_ip)

    # null_count 같은 새 카운터도, get_recent_packets_by_flag() 같은 별도 메서드도
    # 쓰지 않고, FlowManager가 이미 채워주는 flow.recent_packets(최근 10초 윈도우)를
    # 직접 순회해서 NULL 패킷(tcp_flags가 빈 값)만 센다.
    scan_count = sum(
        1 for p in flow.recent_packets
        if not (p.tcp_flags or "")
    )

    if (
        len(unique_ports) >= PORT_THRESHOLD
        and scan_count >= PORT_THRESHOLD
        and flow.pps >= PPS_THRESHOLD
    ):

        print(
            f"[NULL Scan Detected]",
            f"src={packet.src_ip}",
            f"ports={sorted(unique_ports)}",
            f"null={scan_count}",
            f"pps={flow.pps:.2f}"
        )
        return (True, "NULL Scan")
    return (False, "")