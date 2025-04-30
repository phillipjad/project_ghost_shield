import threading
import time
from queue import Queue

from socket_lib.tcp_socket import TCPSocket


def simple_server(port: int):
    server_sock = TCPSocket()
    queue = Queue()

    server_sock.bind_and_listen(ip="127.0.0.1", port=port)

    conn, addr = server_sock.accept()
    print(f"Server on port {port} accepted connection from {addr}")

    listen_thread = threading.Thread(target=conn.listen, args=(queue,), daemon=True)
    listen_thread.start()

    timeout_s = 5
    start_time = time.time()
    received = None

    while time.time() - start_time < timeout_s:
        if not queue.empty():
            received = queue.get()
            break
        time.sleep(0.1)

    if received:
        print(f"Server on port {port} received: {received}")
        conn.send_message(f"Hello from Server {port}".encode())
    else:
        print(f"Server on port {port} timed out waiting for message.")

    time.sleep(1)
    conn.disconnect()
    server_sock.disconnect()


def test_single_socket_multiple_servers():
    server1 = threading.Thread(target=simple_server, args=(50060,), daemon=True)
    server2 = threading.Thread(target=simple_server, args=(50061,), daemon=True)
    server1.start()
    server2.start()

    time.sleep(1)

    conn = TCPSocket()
    queue = Queue()

    conn.connect(ip="127.0.0.1", port=50060)
    listen_thread = threading.Thread(target=conn.listen, args=(queue,), daemon=True)
    listen_thread.start()

    conn.send_message(b"Hello Server 1!")
    time.sleep(1)

    conn.disconnect()

    time.sleep(1)

    conn.connect(ip="127.0.0.1", port=50061)
    listen_thread = threading.Thread(target=conn.listen, args=(queue,), daemon=True)
    listen_thread.start()

    conn.send_message(b"Hello Server 2!")
    time.sleep(1)

    conn.disconnect()

    while not queue.empty():
        msg = queue.get()
        print(f"Received: {msg}")


if __name__ == "__main__":
    test_single_socket_multiple_servers()
