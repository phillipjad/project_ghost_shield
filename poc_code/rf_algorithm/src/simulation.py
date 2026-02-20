import argparse
import multiprocessing as mp
import signal
from envManager import Enviroment_Manager

PROCESS_LIST: list[mp.Process] = []

def input(key):
    # Access environment through the singleton
    env = Enviroment_Manager.instance.environment
    if env:
        if key == 'q' and env.camera_mode == 'editor':
            env.toggle_camera()
        elif key == 'e' and env.camera_mode == 'first_person':
            env.toggle_camera()


def main():
    mp.set_start_method("spawn", force=True)
    manager = Enviroment_Manager()
    manager.run(PROCESS_LIST)

def sig_handler(sig: any, frame: any) -> None:
    for p in PROCESS_LIST:
        if p.is_alive():
            p.terminate()
    for p in PROCESS_LIST:
        p.join()
    exit(0)


if __name__ == '__main__':
    try:
        mp.set_start_method("spawn", force=True)
        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

        parser = argparse.ArgumentParser(
            prog="Project Ghost Shield - RF Simulation",
            description="***Proof of Concept Simulation for Project Ghost Shield***",
        )
        parser.add_argument(
            "-r",
            "--release",
            action="store_true",
            help="If flag is set to true, it runs the program in release mode instead of debug.",
        )
        args = parser.parse_args()
        release = args.release
        main()
        sig_handler(None, None)
    except KeyboardInterrupt:
        sig_handler(None, None)
    except Exception as e:
        print(f"Unhandled exception: {e}")
        sig_handler(None, None)
