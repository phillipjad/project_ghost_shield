from copy import copy
from queue import Queue
from threading import Thread
import time

from mc_lib.multicast_client import MulticastClient
from mc_lib.multicast_server import MulticastServer
from nacl.signing import SignedMessage

from constants.messaging_constants import MSG_INT_STR_MAP, MSG_STR_E, MSG_STR_INT_MAP
from utils.vector import Vector
from message import Message


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
        return len(self.registered_drone_ids)

    def listen(self, internal_msg_queue: Queue) -> None:
        self.mcast_rec_sock.listen(internal_msg_queue)

    def process(self, internal_msg_queue: Queue, controller_send_queue: Queue) -> None:
        while (msg := internal_msg_queue.get()) is not None:
            if (Message.get_source_id(msg).decode() == self.id):
                continue 
            if (msg.startswith('Error')):
                print(f'ERROR ENCOUNTERED!')
                continue
            if (Message.get_msg_type(msg) == MSG_STR_INT_MAP[MSG_STR_E.CONFIRM_REGISTRATION]):
                controller_send_queue.put(1)
                print("YAYAYYAYYYAYAYAYAYYAYAY")

    def main_thread_runner(self, controller_recv_queue: Queue) -> None:
        """Main thread activity 
        """

        # Blocks on .get()
        while True:
            if controller_recv_queue.qsize() >= 1 and (msg_type := controller_recv_queue.get()) is not None:
                # Currently architecting to be msg_type: str and args as list[<arg_types>]
                print(msg_type)
                msg_type, args = msg_type
                if msg_type in MSG_INT_STR_MAP:
                    msg = Message.serialize_msg(msg_type, args)
                    if (msg):
                        Thread(target=send_registration_message, args=[msg, self.mcast_send_sock], daemon=True).start()

def send_registration_message(msg: SignedMessage, socket: MulticastServer, timeout: int = 100000000):
    timeout = time.time() + timeout
    while (time.time() <= timeout):
        socket.send_message(msg)


def start_controller_thread(
    controller_id: str, controller_recv_queue: Queue, controller_send_queue: Queue, x: float, y: float, z: float
) -> None:

    c = Controller(controller_id, x, y, z)
    internal_msg_queue = Queue()

    listener_thread = Thread(target=c.listen, args=[internal_msg_queue], daemon=True)
    processing_thread = Thread(target=c.process, args=[internal_msg_queue, controller_send_queue], daemon=True)
    listener_thread.start()
    processing_thread.start()

    c.main_thread_runner(controller_recv_queue)
