import socket
import struct

# from threading import Thread


def main() -> None:
    mcast_grp = "224.0.0.1"
    mcast_port = 12345

    multicast_client = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
    )
    multicast_client.settimeout(5.0)
    multicast_client.bind(("", mcast_port))
    mreq = struct.pack("4sl", socket.inet_aton(mcast_grp), socket.INADDR_ANY)
    multicast_client.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    multicast_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    while True:
        try:
            print("RECEIVING")
            data, addr = multicast_client.recvfrom(1000)
            print(f"Received message: {data.decode()} from {addr}")
        except TimeoutError:
            print("TIMED OUT!")


if __name__ == "__main__":
    main()
