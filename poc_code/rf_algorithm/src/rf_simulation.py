from drone import Drone
from time import sleep
from field import Field

def main():
    drone_list = [Drone(id, 0, 0, 0) for id in range(4)]

    drone_field = Field(10, 10, None, drone_list)

    print(drone_field)
    drone_field.randomly_place_drones()
    print(drone_field)
    while drone_field.drones_are_equidistant() is not True:
        drone_field.space_drones()
        print("whoops")
        sleep(1)


if __name__ == "__main__":
    main()
