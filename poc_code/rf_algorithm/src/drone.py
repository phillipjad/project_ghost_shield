from queue import Queue
from threading import Thread

from mc_lib.multicast_client import MulticastClient
from mc_lib.multicast_server import MulticastServer
from message import Message
from constants.messaging_constants import MSG_STR_E, MSG_STR_INT_MAP

from utils.vector import Vector

DRN_QUEUE: Queue = Queue()

class Drone:
    """Class representing a rudimentary drone. Capable of moving and broadcasting location"""

    def __init__(
        self, id: str, x_coordinate: float, y_coordinate: float, z_coordinate: float
    ) -> None:
        self.id = id
        self.x = x_coordinate
        self.y = y_coordinate
        self.z = z_coordinate
        self.mcast_send_sock = MulticastServer(port=50000)  # Depends on backlog item
        self.mcast_rec_sock = MulticastClient(port=50001)  # Depends on backlog item

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

    def process(self, msg_queue: Queue) -> None:
        while (msg := msg_queue.get()) is not None:
            if (Message.get_msg_type(msg) == MSG_STR_INT_MAP[MSG_STR_E.CONFIRM_REGISTRATION]):
                print("YAYAYYAYYYAYAYAYAYYAYAY")

    def main_thread_runner(self) -> None:
        """Main thread activity
        """
        # Blocks on .get()
        while (msg_type := .get()) is not None:
            # Currently architecting to be msg_type: str and args as list[<arg_types>]
            msg_type, args = msg_type
            if msg_type in MSG_STR_INT_MAP:
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
    sending_queue = Queue()

    listener_thread = Thread(target=d.listen, args=[listener_queue])
    sending_thread = Thread(target=d.send, args=[sending_queue])
    listener_thread.start()
    sending_thread.start()
