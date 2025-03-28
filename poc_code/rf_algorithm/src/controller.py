from copy import copy
from queue import Queue
from threading import Thread

from utils.vector import Vector
from constants.messaging_constants import ctrl_send_reg_msg, SOCKET_MESSAGE_TYPES
from mc_lib.multicast_server import MulticastServer
from mc_lib.multicast_client import MulticastClient

CTRL_QUEUE: Queue

class Controller:
    def __init__(self, x: float, y: float, z: float, port: int = 50000) -> None:
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
        reg_msg: bytes = Message.registration()
        self.mcast_send_sock.send_message(reg_msg)

    def receive_registration_message(self) -> None:
        """Used to receive registration messages.

        Raises:
            NotImplementedError: _description_
        """
        # This one will put into 

        raise NotImplementedError

    def listen(self, msg_queue: Queue) -> None:
        self.mcast_rec_sock.listen(msg_queue)

    def process_recv(self, msg_queue: Queue) -> None:
        while (msg_queue.get()):
            # Process message
            pass

    def main_thread_runner(self):
        global CTRL_QUEUE

        # Blocks on .get()
        while (msg_type := CTRL_QUEUE.get()) is not None:
            assert(isinstance(msg_type, str))
            self.mcast_send_sock.send_message(msg_type.encode())


def start_controller_thread(x: float, y: float, z: float, controller_queue: Queue) -> None:
    global CTRL_QUEUE

    CTRL_QUEUE = controller_queue
    c = Controller(x, y, z)
    q = Queue()

    listener_thread = Thread(target=c.listen, args=[q], daemon=True)
    processing_thread = Thread(target=c.receive, args=[q], daemon=True)
    listener_thread.start()
    processing_thread.start()

    c.main_thread_runner()
