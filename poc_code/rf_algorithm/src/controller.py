import time
from copy import copy
from queue import Queue
from threading import Thread, Timer

from socket_lib.multicast_client import MulticastClient
from socket_lib.multicast_server import MulticastServer
from socket_lib.tcp_socket import TCPSocket
from nacl.signing import SignedMessage

from constants.messaging_constants import MSG_INT_STR_MAP, MSG_STR_E, MSG_STR_INT_MAP
from message import Message
from utils.vector import Vector

ack_queue: Queue[SignedMessage] = Queue()

class Controller:
    def __init__(
        self, id: str, x: float, y: float, z: float, port: int = 50000
    ) -> None:
        self.id = id
        self.location = Vector(x, y, z)
        self.registered_drone_ids: set[str] = set()
        self.mcast_send_sock = MulticastServer(port=port)
        self.mcast_rec_sock = MulticastClient(port=port)
        self.tcp_send_sock = TCPSocket()
        self.tcp_rec_sock = TCPSocket()

    def get_location(self) -> Vector:
        return copy(self.location)

    def register_drone(self, drone_id: str) -> bool:
        """Registers a drone to the controller. Returns true if successful, false otherwise.

        Args:
            drone_id (str): ID of a drone.

        Returns:
            bool: True if successful, false otherwise.
        """
        prev_len = len(self.registered_drone_ids)
        self.registered_drone_ids.add(drone_id)
        return prev_len < len(self.registered_drone_ids)

    def get_num_registered_drones(self) -> int:
        return len(self.registered_drone_ids)

    def listen_udp(self, internal_msg_queue: Queue) -> None:
        self.mcast_rec_sock.listen(internal_msg_queue)

    def listen_tcp(self, ip: str, port: int) -> None:
        global ack_queue

        self.tcp_rec_sock.bind_and_listen(ip=ip, port=port)
        while True:
            conn, _ = self.tcp_rec_sock.accept()
            listener_thread = Thread(target=conn.listen, args=[ack_queue], daemon=True)
            listener_thread.start()
            listener_thread.join(timeout=0.5)
            conn.disconnect()

    def process(self, internal_msg_queue: Queue, controller_send_queue: Queue) -> None:
        while (msg := internal_msg_queue.get()) is not None:
            if Message.get_source_id(msg) == self.id:
                continue
            if msg.startswith(b"ERROR"):
                print("ERROR ENCOUNTERED!")
                continue
            if (
                Message.get_msg_type(msg)
                == MSG_STR_INT_MAP[MSG_STR_E.CONFIRM_REGISTRATION]
            ):
                confirm_reg_msg = Message.deserialize_msg(msg)
                drone_id: str = confirm_reg_msg.payload.drone_id
                self.registered_drone_ids.add(drone_id)
            elif (Message.get_msg_type(msg) == MSG_STR_INT_MAP[MSG_STR_E.CURRENT_LOCATION]):
                location_msg = Message.deserialize_msg(msg)
                drone_id: str = Message.get_source_id(msg)
                x: float = location_msg.payload.x
                y: float = location_msg.payload.y
                z: float = location_msg.payload.z
                controller_send_queue.put((x, y, z))

    def send_num_drones_registered(self, controller_send_queue: Queue) -> None:
        """Sends the number of registered drones to the controller send queue.
        This is a blocking call.

        Args:
            controller_send_queue (Queue): _description_
        """
        print(f"Controller {self.id} sending number of registered drones")
        num_drones_registered = self.get_num_registered_drones()
        controller_send_queue.put(num_drones_registered)

    def main_thread_runner(
        self, controller_recv_queue: Queue[tuple[int, list[any], any]], controller_send_queue: Queue[any]
    ) -> None:
        """Main thread activity"""

        # Blocks on .get()
        while True:
            if (command := controller_recv_queue.get()) is not None:
                # Currently architecting to be msg_type: str and args as list[<arg_types>]
                msg_type, args, extra_var = command
                if msg_type in MSG_INT_STR_MAP:
                    msg = Message.serialize_msg(msg_type, args)
                    if msg_type == MSG_STR_INT_MAP[MSG_STR_E.ENABLE_REGISTRATION]:
                        Thread(
                            target=send_registration_message,
                            args=[msg, self.mcast_send_sock, extra_var - 0.5],
                            daemon=True,
                        ).start()
                        # Minus 0.5 so that we can be sure the main thread is responded to before it stops listening
                        main_thread_response_timer = Timer(
                            interval=extra_var - 0.5,
                            function=self.send_num_drones_registered,
                            args=[controller_send_queue],
                        )
                        main_thread_response_timer.start()
                    elif msg_type == MSG_STR_INT_MAP[MSG_STR_E.GET_LOCATION]:
                        # Start thread to send location request to drone
                        Thread(
                            target=send_get_location_message,
                            args=[msg, self.tcp_send_sock, *extra_var],
                            daemon=True,
                        ).start()


def send_registration_message(
    msg: SignedMessage, socket: MulticastServer, timeout: int = 10
) -> None:
    timeout = time.time() + timeout
    while time.time() <= timeout:
        socket.send_message(msg)
        time.sleep(0.5)

def send_get_location_message(
    msg: SignedMessage, tcp_socket: TCPSocket, ip: str, port: int, timeout: int = 5 
) -> None:
    ack: SignedMessage | None = None
    tcp_socket.connect(ip=ip, port=port)
    # After connect we now have a socket. Add timeout
    tcp_socket.send_message(msg)

    try:
        ack = ack_queue.get(timeout=1)
    except Exception:
        pass
    if ack is None or Message.get_msg_type(ack) != MSG_STR_INT_MAP[MSG_STR_E.COMMAND_ACK]:
        print(f"Drone at {ip}:{port} did not respond with an ACK")
        return
    tcp_socket.disconnect()

    


def send_ack(
    msg: SignedMessage, tcp_socket: TCPSocket, ip: str, port: int, timeout: int = 2
) -> None:
    tcp_socket.connect(ip=ip, port=port)
    # After connect we now have a socket. Add timeout
    tcp_socket.sock.settimeout(timeout)
    #Send ack
    tcp_socket.send_message(msg)
    tcp_socket.disconnect()


def start_controller_thread(
    controller_id: str,
    controller_recv_queue: Queue,
    controller_send_queue: Queue,
    x: float,
    y: float,
    z: float,
    ip: str,
    port: int,
) -> None:
    c = Controller(controller_id, x, y, z)
    internal_msg_queue: Queue[tuple[int, list]] = Queue()

    listener_thread_udp = Thread(target=c.listen_udp, args=[internal_msg_queue], daemon=True)
    listener_thread_tcp = Thread(target=c.listen_tcp, args=[ip, port], daemon=True)
    processing_thread = Thread(target=c.process, args=[internal_msg_queue, controller_send_queue], daemon=True)
    listener_thread_udp.start()
    listener_thread_tcp.start()
    processing_thread.start()

    c.main_thread_runner(controller_recv_queue, controller_send_queue)
