from time import sleep

from drone import Drone
from field import Field


def main() -> None:
    drone_list = [Drone(id, 0, 0, 0) for id in range(4)]

    # Equidistant list of drones
    # drone_list = [
    #     Drone(0, 3, 3, 3),
    #     Drone(1, 3, -3, -3),
    #     Drone(2, -3, 3, -3),
    #     Drone(3, -3, -3, 3)
    # ]

    drone_field = Field(10, 10, None, drone_list)

    print(drone_field)
    drone_field.randomly_place_drones()
    print(drone_field)
    while drone_field.drones_are_equidistant() is not True:
        drone_field.space_drones()
        print("STILL NOT EQUIDISTANT")
        sleep(1)
    else:
        print("EQUIDISTANT!")


if __name__ == "__main__":
    main()
