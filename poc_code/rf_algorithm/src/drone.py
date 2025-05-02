from queue import Queue
from threading import Thread
import time

from nacl.signing import SignedMessage
from socket_lib.multicast_client import MulticastClient
from socket_lib.multicast_server import MulticastServer
from socket_lib.tcp_socket import TCPSocket

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
        drone_tcp_ip: str,
        drone_tcp_port: int,
        is_process: bool = True,
        port: int = 50000,
    ) -> None:
        self.id = id
        self.x = x_coordinate
        self.y = y_coordinate
        self.z = z_coordinate
        self.drone_tcp_ip = drone_tcp_ip
        self.drone_tcp_port = drone_tcp_port
        if is_process:
            self.mcast_send_sock = MulticastServer(port=port)
            self.mcast_rec_sock = MulticastClient(port=port)
            self.tcp_send_sock = TCPSocket()
            self.tcp_rec_sock = TCPSocket()

    def move_x(self, distance: float) -> None:
        """Moves the drone in the x direction by a given distance."""
        self.x += distance

    def move_y(self, distance: float) -> None:
        """Moves the drone in the y direction by a given distance."""
        self.y += distance

    def move_z(self, distance: float) -> None:
        """Moves the drone in the z direction by a given distance."""
        self.z += distance

    def move_from_vector(self, vector: Vector) -> None:
        """
        Moves the drone according to the given 3D movement vector.

        If the vector has zero magnitude, no movement occurs. Otherwise,
        the drone is moved in the x, y, and z directions based on the vector's components.

        Args:
            vector (Vector): A 3D vector representing the movement direction and magnitude.
        """
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
        """Sets the x coordinate of the drone."""
        self.x = x

    def set_y(self, y: float) -> None:
        """Sets the y coordinate of the drone."""
        self.y = y

    def set_z(self, z: float) -> None:
        """Sets the z coordinate of the drone."""
        self.z = z

    def get_x(self) -> float:
        """Returns the x coordinate of the drone."""
        return self.x

    def get_y(self) -> float:
        """Returns the y coordinate of the drone."""
        return self.y

    def get_z(self) -> float:
        """Returns the z coordinate of the drone."""
        return self.z

    def get_id(self) -> str:
        """Returns the id of the drone."""
        return self.id

    def listen_udp(self, listener_queue: Queue) -> None:
        """Listen for incoming UDP messages and add them to the listener queue.

        Args:
            listener_queue (Queue): The queue to which incoming messages will be added.
        """        
        self.mcast_rec_sock.listen(listener_queue)

    def listen_tcp(self, listener_queue: Queue, ip: str, port: int) -> None:
        """Listen for incoming TCP connections and spawn a thread to handle each connection.

        Args:
            listener_queue (Queue): The queue to which incoming messages will be added.
            ip (str): The IP address to bind the TCP socket to.
            port (int): The port to bind the TCP socket to.
        """        
        self.tcp_rec_sock.bind_and_listen(ip=ip, port=port)
        while True:
            conn, _ = self.tcp_rec_sock.accept()
            listener_thread = Thread(target=conn.listen, args=[listener_queue], daemon=True)
            listener_thread.start()
            listener_thread.join(timeout=0.5)
            conn.disconnect()

    def process(
        self, listener_queue: Queue[bytes], internal_msg_queue: Queue, controller_tcp_ip: str, controller_tcp_port: int
    ) -> None:
        """Process incoming messages from the listener queue and handle them accordingly.

        Args:
            listener_queue (Queue[bytes]): The queue from which incoming messages will be read.
            internal_msg_queue (Queue): The queue to which processed messages will be added.
            controller_tcp_ip (str): The IP address of the controller.
            controller_tcp_port (int): The port of the controller.
        """        
        while (msg := listener_queue.get()) is not None:
            if Message.get_source_id(msg) == self.id:
                continue
            if msg.startswith(b"ERROR"):
                print("ERROR ENCOUNTERED!")
                continue
            if Message.get_msg_type(msg) == MSG_STR_INT_MAP[MSG_STR_E.GET_LOCATION]:
                ack_msg = Message.serialize_msg(MSG_STR_INT_MAP.get(MSG_STR_E.COMMAND_ACK), [self.id])
                # Send quick ack
                ack_thread = Thread(
                    target=send_ack,
                    args=[ack_msg, self.tcp_send_sock, controller_tcp_ip, controller_tcp_port],
                )
                ack_thread.start()

                # Send location over multicast
                internal_msg_queue.put(
                    (
                        MSG_STR_INT_MAP[MSG_STR_E.CURRENT_LOCATION],
                        [self.id, self.x, self.y, self.z],
                    )
                )
                ack_thread.join()
            elif Message.get_msg_type(msg) == MSG_STR_INT_MAP[MSG_STR_E.ENABLE_REGISTRATION]:
                internal_msg_queue.put((MSG_STR_INT_MAP.get(MSG_STR_E.CONFIRM_REGISTRATION), [self.id]))
            elif Message.get_msg_type(msg) == MSG_STR_INT_MAP[MSG_STR_E.MOVE_LOCATION]:
                # Send quick ack
                ack_msg = Message.serialize_msg(MSG_STR_INT_MAP.get(MSG_STR_E.COMMAND_ACK), [self.id])
                ack_thread = Thread(
                    target=send_ack,
                    args=[ack_msg, self.tcp_send_sock, controller_tcp_ip, controller_tcp_port],
                )
                ack_thread.start()
                move_msg = Message.deserialize_msg(msg)
                x: float = move_msg.payload.x
                y: float = move_msg.payload.y
                z: float = move_msg.payload.z
                self.set_x(x)
                self.set_y(y)
                self.set_z(z)
                internal_msg_queue.put(
                    (
                        MSG_STR_INT_MAP[MSG_STR_E.CURRENT_LOCATION],
                        [self.id, self.x, self.y, self.z],
                    )
                )
                ack_thread.join()
            elif Message.get_msg_type(msg) == MSG_STR_INT_MAP[MSG_STR_E.ENABLE_JAMMER]:
                enable_jammer_msg = Message.deserialize_msg(msg)
                duration: float = enable_jammer_msg.payload.duration
                jamming_thread = Thread(
                    target=send_jamming_msg,
                    args=[self.id, self.mcast_send_sock, duration],
                    daemon=True
                )
                jamming_thread.start()
                jamming_thread.join(duration)
            else:
                pass
                # print(f'Unknown {msg=}')

    def main_thread_runner(self, internal_msg_queue: Queue[tuple[int, list]]) -> None:
        """Main thread activity"""
        # Blocks on .get()
        while (command := internal_msg_queue.get()) is not None:
            msg_type, args = command
            if msg_type in MSG_INT_STR_MAP:
                msg = Message.serialize_msg(msg_type, args)
                self.mcast_send_sock.send_message(msg)

    def pretty_print(self) -> str:
        """Pretty prints the drone's id and coordinates."""     
        return f"Drone {self.id}"

    def __str__(self) -> str:
        """Returns a string representation of the drone's id and coordinates."""      
        return f"""
            Drone {self.id}
            X Coordinate: {self.x}
            Y Coordinate: {self.y}
            Z Coordinate: {self.z}
        """

    def __repr__(self) -> str:
        """Returns a string representation of the drone's id and coordinates for debugging."""
        return f"ID: {self.id}\nX: {self.x}\nY: {self.y}\nZ: {self.z}\n"

    # checks if two drones are equal by id, x, y, and z
    def __eq__(self, other) -> bool:
        """Compares two Drone objects for equality based on their id and coordinates.

        Args:
            self (_type_): The current Drone object.
            other (_type_): The other Drone object to compare against.

        Returns:
            bool: True if the drones are equal (same id and coordinates), False otherwise.
        """        
        if not isinstance(other, Drone):
            return False  # don't attempt to compare against unrelated types
        if (
            self.id == other.id
            and self.x == other.get_x()
            and self.y == other.get_y()
            and self.z == other.get_z()
        ):
            return True
        return False


def send_ack(msg: SignedMessage, tcp_socket: TCPSocket, ip: str, port: int, timeout: int = 1) -> None:
    tcp_socket.connect(ip=ip, port=port)
    # After connect we now have a socket. Add timeout
    tcp_socket.sock.settimeout(timeout)
    # Send ack
    tcp_socket.send_message(msg)
    tcp_socket.disconnect()

def send_jamming_msg(drone_id: str, mcast_send_sock: MulticastServer, duration: float) -> None:
    """Sends a jamming message to the drone for a given duration.

    Args:
        drone_id (str): id of the drone
        mcast_send_sock (MulticastServer): MulticastServer object used for sending the message
        duration (float): duration for which the jamming message should be sent
    """    
    timeout = time.time() + duration
    while time.time() <= timeout:
        msg = Message.serialize_msg(MSG_STR_INT_MAP[MSG_STR_E.JAMMER_ENABLED], [drone_id])
        mcast_send_sock.send_message(msg)

def start_drone_process(
    id: str,
    x: float,
    y: float,
    z: float,
    drone_tcp_ip: str,
    drone_tcp_port: int,
    controller_tcp_ip: str,
    controller_tcp_port: int,
) -> None:
    """Starts the drone process by initializing the drone and starting the necessary threads.

    Args:
        id (str): id of the drone
        x (float): x coordinate of the drone
        y (float): y coordinate of the drone
        z (float): z coordinate of the drone
        drone_tcp_ip (str): ip address of the drone
        drone_tcp_port (int): port of the drone
        controller_tcp_ip (str): ip address of the controller
        controller_tcp_port (int): port of the controller
    """    
    d = Drone(id, x, y, z, drone_tcp_ip, drone_tcp_port)
    listener_queue: Queue[bytes] = Queue()
    internal_msg_queue: Queue[tuple[int, list]] = Queue()

    udp_listener_thread = Thread(target=d.listen_udp, args=[listener_queue], daemon=True)
    processing_thread = Thread(
        target=d.process, args=[listener_queue, internal_msg_queue, controller_tcp_ip, controller_tcp_port], daemon=True
    )
    tcp_listener_thread = Thread(target=d.listen_tcp, args=[listener_queue, drone_tcp_ip, drone_tcp_port], daemon=True)
    udp_listener_thread.start()
    tcp_listener_thread.start()
    processing_thread.start()

    d.main_thread_runner(internal_msg_queue)
