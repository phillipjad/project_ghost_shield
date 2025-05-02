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


def main(movement_queue: Queue, initialize_queue: Queue):
    manager = Enviroment_Manager()
    manager.run(movement_queue, initialize_queue)


if __name__ == '__main__':
    main()
