import socket
from threading import Thread


def main():
    multicast_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    print("Hello from ghost-shield-mc-client!")


if __name__ == "__main__":
    main()