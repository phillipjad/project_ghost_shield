from copy import copy
from queue import Queue
from threading import Thread

from mc_lib.multicast_client import MulticastClient
from mc_lib.multicast_server import MulticastServer
from nacl.signing import SignedMessage

from constants.messaging_constants import MSG_STR_E, MSG_STR_INT_MAP
from utils.vector import Vector
from message import Message

CTRL_QUEUE: Queue


class Controller:
    def __init__(
        self, id: str, x: float, y: float, z: float, port: int = 50000
    ) -> None:
        self.id = id
        self.location = Vector(x, y, z)
        self.registered_drone_ids: set[str] = set()
        self.mcast_send_sock = MulticastServer(port=port)
        self.mcast_rec_sock = MulticastClient(port=port)

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
        return len(self.register_drone_ids)

    def send_registration_message(self) -> None:
        """Used to broadcast message over multicast alerting drones they can register.

        Raises:
            NotImplementedError: _description_
        """
        reg_msg: bytes = (
            Message.process(MSG_STR_E.ENABLE_REGISTRATION) if False else b"REGISTRATION"
        )
        self.mcast_send_sock.send_message(reg_msg)

    def receive_registration_message(self) -> None:
        """Used to receive registration messages.

        Raises:
            NotImplementedError: _description_
        """

        raise NotImplementedError

    def listen(self, msg_queue: Queue) -> None:
        self.mcast_rec_sock.listen(msg_queue)

    def process(self, msg_queue: Queue) -> None:
        while (msg := msg_queue.get()) is not None:
            if (Message.get_msg_type(msg) == MSG_STR_INT_MAP[MSG_STR_E.CONFIRM_REGISTRATION]):
                print("YAYAYYAYYYAYAYAYAYYAYAY")

    def main_thread_runner(self) -> None:
        """Main thread activity 
        """
        global CTRL_QUEUE

        # Blocks on .get()
        while (msg_type := CTRL_QUEUE.get()) is not None:
            # Currently architecting to be msg_type: str and args as list[<arg_types>]
            msg_type, args = msg_type
            if msg_type in MSG_STR_INT_MAP:
                msg = Message.serialize_msg(msg_type, args)
                self.mcast_send_sock.send_message(msg)


def start_controller_thread(
    controller_id: str, x: float, y: float, z: float, controller_queue: Queue
) -> None:
    global CTRL_QUEUE

    CTRL_QUEUE = controller_queue
    c = Controller(controller_id, x, y, z)
    q = Queue()

    listener_thread = Thread(target=c.listen, args=[q], daemon=True)
    processing_thread = Thread(target=c.process, args=[q], daemon=True)
    listener_thread.start()
    processing_thread.start()

    c.main_thread_runner()
