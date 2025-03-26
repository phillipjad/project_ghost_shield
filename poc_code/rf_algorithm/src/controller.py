from copy import copy
from queue import Queue
from threading import Thread

from utils.vector import Vector
from constants.messaging_constants import ctrl_send_reg_msg

CTRL_QUEUE: Queue

class Controller:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.location = Vector(x, y, z)
        self.registered_drone_ids: set[str] = set()
        self.mcast_send_sock = None  # Depends on backlog item
        self.mcast_rec_sock = None  # Depends on backlog item

    def get_location(self) -> Vector:
        return copy(self.location)

    def get_mcast_send_sock(self) -> None:
        return self.mcast_send_sock

    def get_mcast_rec_sock(self) -> None:
        return self.mcast_rec_sock

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
        raise NotImplementedError

    def receive_registration_message(self) -> None:
        """Used to receive registration messages.

        Raises:
            NotImplementedError: _description_
        """
        # This one will put into 
        raise NotImplementedError

    def listen(self, msg_queue: Queue) -> None:
        raise NotImplementedError

    def send(self, msg_queue: Queue) -> None:
        raise NotImplementedError

    def main_thread_listener(self):
        # Blocks on .get()
        while (msg := CTRL_QUEUE.get()) is not None:
            if msg == ctrl_send_reg_msg:
                self.send_registration_message()
            else:
                continue 


def start_controller_thread(x: float, y: float, z: float, controller_queue: Queue) -> None:
    c = Controller(x, y, z)
    q = Queue()
    CTRL_QUEUE = controller_queue

    listener_thread = Thread(target=c.listen, args=[q], daemon=True)
    sending_thread = Thread(target=c.send, args=[q], daemon=True)
    listener_thread.start()
    sending_thread.start()
    c.main_thread_listener()