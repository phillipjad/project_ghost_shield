from queue import Queue
from threading import Thread

from socket_lib.multicast_client import MulticastClient
from socket_lib.multicast_server import MulticastServer
from socket_lib.tcp_server import TCPServer 
from socket_lib.tcp_client import TCPClient 

from constants.messaging_constants import MSG_INT_STR_MAP, MSG_STR_E, MSG_STR_INT_MAP
from message import Message
from utils.vector import Vector


class Drone:
    """Class representing a rudimentary drone. Capable of moving and broadcasting location"""

    def __init__(
        self,
        id: str,
        x_coordinate: float,
        y_coordinate: float,
        z_coordinate: float,
        port: int = 50000,
    ) -> None:
        self.id = id
        self.x = x_coordinate
        self.y = y_coordinate
        self.z = z_coordinate
        self.mcast_send_sock = MulticastServer(port=port)
        self.mcast_rec_sock = MulticastClient(port=port)
        self.tcp_send_sock = TCPServer(port=port)
        self.tcp_rec_sock = TCPClient(port=port)

    def move_x(self, distance: float) -> None:
        self.x += distance

    def move_y(self, distance: float) -> None:
        self.y += distance

    def move_z(self, distance: float) -> None:
        self.z += distance

    def move_from_vector(self, vector: Vector) -> None:
        # check if vector has exactly 3 components
        # checks if there should be no movement at all
        if vector.get_magnitude() == 0.0:
            print("No movement")
            return

        vector_components = vector.get_internals_as_tuple()

        # print the movement vector
        print(
            f"Moving {self.pretty_print()} by x: {vector_components[0]}, y: {vector_components[1]}, z: {vector_components[2]}"
        )

        # moves the drone in the x, y, and z directions
        self.move_x(vector_components[0])
        self.move_y(vector_components[1])
        self.move_z(vector_components[2])

    def set_x(self, x: float) -> None:
        self.x = x

    def set_y(self, y: float) -> None:
        self.y = y

    def set_z(self, z: float) -> None:
        self.z = z

    def get_x(self) -> float:
        return self.x

    def get_y(self) -> float:
        return self.y

    def get_z(self) -> float:
        return self.z

    def get_id(self) -> str:
        return self.id

    def listen(self, msg_queue: Queue) -> None:
        self.mcast_rec_sock.listen(msg_queue)

    def process(self, msg_queue: Queue, internal_msg_queue: Queue) -> None:
        while (msg := msg_queue.get()) is not None:
            if Message.get_source_id(msg) == self.id:
                continue
            if msg.startswith(b"ERROR"):
                print("ERROR ENCOUNTERED!")
                continue
            if (
                Message.get_msg_type(msg)
                == MSG_STR_INT_MAP[MSG_STR_E.ENABLE_REGISTRATION]
            ):
                internal_msg_queue.put(
                    (MSG_STR_INT_MAP.get(MSG_STR_E.CONFIRM_REGISTRATION), [self.id])
                )

    def main_thread_runner(self, internal_msg_queue: Queue) -> None:
        """Main thread activity"""
        # Blocks on .get()
        while (command := internal_msg_queue.get()) is not None:
            msg_type, args = command
            if msg_type in MSG_INT_STR_MAP:
                msg = Message.serialize_msg(msg_type, args)
                self.mcast_send_sock.send_message(msg)

    def pretty_print(self) -> str:
        return f"Drone {self.id}"

    def __str__(self) -> str:
        return f"""
            Drone {self.id}
            X Coordinate: {self.x}
            Y Coordinate: {self.y}
            Z Coordinate: {self.z}
        """

    def __repr__(self) -> str:
        return f"ID: {self.id}\nX: {self.x}\nY: {self.y}\nZ: {self.z}\n"


def start_drone_process(id: str, x: float, y: float, z: float) -> None:
    d = Drone(id, x, y, z)
    listener_queue = Queue()
    internal_msg_queue = Queue()

    listener_thread = Thread(target=d.listen, args=[listener_queue], daemon=True)
    processing_thread = Thread(
        target=d.process, args=[listener_queue, internal_msg_queue], daemon=True
    )
    listener_thread.start()
    processing_thread.start()

    d.main_thread_runner(internal_msg_queue)
