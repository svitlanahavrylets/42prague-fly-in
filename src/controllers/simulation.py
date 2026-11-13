from ..models import Drone


class SimulationController:
    def __init__(self, drones: list[Drone]) -> None:
        self.drones = drones

    def _get_drone_action(self, drone: Drone, turn: int) -> str | None:
        for i in range(1, len(drone.path)):
            prev_zone, prev_turn = drone.path[i - 1]
            # print(f"prev_zone '{prev_zone}' prev_turn '{prev_turn}'")
            curr_zone, curr_turn = drone.path[i]
            # print(f"curr_zone '{curr_zone}' curr_turn '{curr_turn}'")

            if curr_turn == turn and prev_zone != curr_zone:
                return f"D{drone.id}-{curr_zone}"
            if prev_turn < turn < curr_turn:
                return f"D{drone.id}-{prev_zone}-{curr_zone}"
        return None

    def _get_max_turn(self) -> int:
        max_turn = 0
        for drone in self.drones:
            if not drone.path:
                raise ValueError(f"Path for Drone {drone.id!r} does not exist")
            print(f"drone in simulation => {drone.path}")

            max_item = drone.path[-1][1]
            if max_item > max_turn:
                max_turn = max_item
        return max_turn

    #     print(f"Turn {self.turn}: ")

    def run(self) -> None:
        max_turn = self._get_max_turn()
        for turn in range(1, max_turn + 1):
            turn_moves: list[str] = []
            for drone in self.drones:
                action = self._get_drone_action(drone, turn)
                # print(f"next drone")
                if action is not None:
                    turn_moves.append(action)
                    # print(f"action {action}")
            if turn_moves:
                # print("before turn_moves")
                print(" ".join(turn_moves))
                # print("after turn_moves")
