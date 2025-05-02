from envManager import Enviroment_Manager


def input(key):
    # Access environment through the singleton
    env = Enviroment_Manager.instance.environment
    if env:
        if key == 'q' and env.camera_mode == 'editor':
            env.toggle_camera()
        elif key == 'e' and env.camera_mode == 'first_person':
            env.toggle_camera()


def main():
    manager = Enviroment_Manager()
    manager.run()


if __name__ == '__main__':
    main()
