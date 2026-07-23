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

    # Xmas 패킷에는 "F"가 포함되어 있어서, flow.fin_count 증가 로직
    # (if "F" in flags: flow.fin_count += 1) 이 Xmas 패킷에도 그대로 적용된다.
    # 따라서 별도의 xmas_count 없이 flow.fin_count를 그대로 재사용할 수 있다.
    scan_count = flow.fin_count

    if (
        len(unique_ports) >= PORT_THRESHOLD
        and scan_count >= PORT_THRESHOLD
        and flow.pps >= PPS_THRESHOLD
    ):

        print(
            f"[Xmas Scan Detected]",
            f"src={packet.src_ip}",
            f"ports={sorted(unique_ports)}",
            f"fin={scan_count}",
            f"pps={flow.pps:.2f}"
        )
        return (True, "Xmas Scan")
    return (False, "")