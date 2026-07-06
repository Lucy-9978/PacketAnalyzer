from engine import PacketData, Flow

def detect(packet: PacketData, flow: Flow):

    print('FIN_flood 모듈 실행중')

    if flow.protocol != "TCP":
        return
    if flow.duration < 1:
        return
    if flow.pps < 1000:
        return
    if flow.packet_count == 0:
        return
    fin_ratio = flow.fin_count / flow.packet_count

    if fin_ratio < 0.8:
        return

    print(f"""
        [FIN Flood]
        해당 IP ={packet.src_ip}\n
        초당 패킷 수 ={flow.pps}\n
        FIN 수 ={flow.fin_count}\n
        총 패킷 중 FIN 비율 ={ack_ratio:.2f}
    """)