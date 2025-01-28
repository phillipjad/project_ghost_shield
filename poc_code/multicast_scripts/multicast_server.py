import socket
import struct
from time import sleep


def main() -> None:
    mcast_grp = "224.0.0.1"
    mcast_port = 12345
    mcast_ttl = b"2"

    multicast_server = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
    )
    multicast_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    multicast_server.setsockopt(
        socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton("0.0.0.0")
    )
    multicast_server.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, mcast_ttl)

    str_message = "Hello World!"
    str_message_len = len(str_message)
    message = struct.pack(
        f"H{str_message_len}s", str_message_len, str_message.encode("utf-8")
    )

    while True:
        print(f"Sending {message}")
        multicast_server.sendto(message, (mcast_grp, mcast_port))
        sleep(1)


if __name__ == "__main__":
    main()
