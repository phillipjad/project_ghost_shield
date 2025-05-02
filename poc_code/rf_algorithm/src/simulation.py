from multiprocessing import Queue
from envManager import Enviroment_Manager


def input(key):
    # Access environment through the singleton
    env = Enviroment_Manager.instance.environment
    if env:
        if key == 'q' and env.camera_mode == 'editor':
            env.toggle_camera()
        elif key == 'e' and env.camera_mode == 'first_person':
            env.toggle_camera()


def main(drones_queue: Queue, positions_queue: Queue, movement_queue: Queue):
    manager = Enviroment_Manager()
    manager.run(drones_queue, positions_queue, movement_queue)


if __name__ == '__main__':
    main()
