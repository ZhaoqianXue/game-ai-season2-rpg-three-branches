"""Ten villagers with stable, recognizable jobs around the village."""

from collections import deque

from sandbox.observation_types import ThreeBranchesAction, ThreeBranchesObservation
from sandbox.village import action, geometry, layout, me, people, props


def _cell_centre(cell: dict[str, int]) -> dict[str, float]:
    """Return the point at the centre of one village cell."""

    return {"x": cell["x"] + 0.5, "y": cell["y"] + 0.5}


class Agent:
    """Assigns each villager a persistent workplace and social mannerism."""

    _JOBS = (
        ("plot", 0, "nod"),
        ("plot", 1, "wave"),
        ("plot", 2, "point"),
        ("plot", 3, "nod"),
        ("plot", 4, "wave"),
        ("shrine", 0, "nod"),
        ("stall", 0, "sweep"),
        ("pump", 0, "shrug"),
        ("board", 0, "point"),
        ("plot", 4, "sweep"),
    )
    _PROP_SIZES = {
        "stall": (2, 2),
        "shrine": (3, 3),
        "board": (2, 2),
        "plot": (4, 2),
        "pump": (1, 1),
    }

    def reset(self, seed: int, observation: ThreeBranchesObservation) -> None:
        """Choose one job from the stable player number."""

        player_number = int(me.player_id(observation).rsplit("_", 1)[1])
        self._player_number = player_number
        self._job = self._JOBS[(player_number - 1) % len(self._JOBS)]
        job_type, job_index, _ = self._job
        matching_props = [prop for prop in props.all(observation) if prop["type"] == job_type]
        self._target = matching_props[job_index % len(matching_props)] if matching_props else None
        self._route_distance = self._build_routes(observation, self._target)

    def act(self, observation: ThreeBranchesObservation) -> ThreeBranchesAction:
        """Choose one simple order from current sight and standing village knowledge."""

        heading = me.heading(observation)
        here = me.position(observation)
        _, _, job_emote = self._job
        if self._player_number > 5 and observation["tick"] < 40:
            return action.stand(heading)
        expression = job_emote if people.seen(observation) else "none"
        home = me.home(observation)
        door = layout.doorway(observation, home) if home != "none" else None
        here_cell = layout.cell_at(observation, here)
        if (
            door is not None
            and here_cell is not None
            and layout.ground_at(observation, here_cell) == "interior"
        ):
            return action.walk(geometry.heading_to(here, door), 1.0, expression)

        target = self._target
        usable = props.usable(observation)
        if target is not None and usable is not None and usable["id"] == target["id"]:
            return action.stand(heading, "use")
        if target is not None:
            current_cell = layout.cell_at(observation, here)
            current_key = None if current_cell is None else (current_cell["x"], current_cell["y"])
            current_distance = None if current_key is None else self._route_distance.get(current_key)
            if current_distance is None and door is not None and geometry.distance(here, door) < 4.0:
                home_record = layout.building(observation, home)
                if home_record is not None:
                    home_centre = {
                        "x": home_record["cell"]["x"] + 4.0,
                        "y": home_record["cell"]["y"] + 3.5,
                    }
                    dx = door["x"] - home_centre["x"]
                    dy = door["y"] - home_centre["y"]
                    scale = max(abs(dx), abs(dy), 1.0)
                    outside = {
                        "x": door["x"] + 2.5 * dx / scale,
                        "y": door["y"] + 2.5 * dy / scale,
                    }
                    return action.walk(geometry.heading_to(here, outside), 1.0, expression)
            if current_distance is not None and current_distance > 0:
                occupied = {
                    (cell["x"], cell["y"])
                    for person in people.nearby(observation)
                    if (cell := layout.cell_at(observation, person["position"])) is not None
                }
                candidates = [
                    neighbor
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (neighbor := (current_key[0] + dx, current_key[1] + dy)) not in occupied
                    and self._route_distance.get(neighbor, current_distance) < current_distance
                ]
                next_cell = (
                    min(
                        candidates,
                        key=lambda cell: (self._route_distance[cell], cell),
                    )
                    if candidates
                    else self._detour_step(observation, current_key, occupied, current_distance)
                )
                if next_cell is not None:
                    destination = _cell_centre({"x": next_cell[0], "y": next_cell[1]})
                    return action.walk(geometry.heading_to(here, destination), 1.0, expression)
            return action.stand(heading, expression)
        return action.walk(heading, 0.0, expression)

    def _build_routes(
        self, observation: ThreeBranchesObservation, target
    ) -> dict[tuple[int, int], int]:
        """Map every reachable cell to its static distance from the assigned prop."""

        if target is None:
            return {}
        width, height = self._PROP_SIZES[target["type"]]
        if target["facing"] in {"east", "west"}:
            width, height = height, width
        x, y = target["cell"]["x"], target["cell"]["y"]
        target_centre = {"x": x + width / 2, "y": y + height / 2}
        border = {
            *((column, y - 1) for column in range(x, x + width)),
            *((column, y + height) for column in range(x, x + width)),
            *((x - 1, row) for row in range(y, y + height)),
            *((x + width, row) for row in range(y, y + height)),
        }
        goals = {
            cell
            for cell in border
            if layout.walkable(observation, {"x": cell[0], "y": cell[1]})
            and layout.line_of_sight(
                observation,
                _cell_centre({"x": cell[0], "y": cell[1]}),
                target_centre,
            )
        }
        queue = deque(goals)
        distances = {cell: 0 for cell in goals}
        while queue:
            toward_goal = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                candidate = (toward_goal[0] + dx, toward_goal[1] + dy)
                if candidate in distances or not layout.can_step(
                    observation,
                    {"x": candidate[0], "y": candidate[1]},
                    {"x": toward_goal[0], "y": toward_goal[1]},
                ):
                    continue
                distances[candidate] = distances[toward_goal] + 1
                queue.append(candidate)
        return distances

    def _detour_step(
        self,
        observation: ThreeBranchesObservation,
        start: tuple[int, int],
        occupied: set[tuple[int, int]],
        start_distance: int,
    ) -> tuple[int, int] | None:
        """Find one temporary sidestep around a character blocking every downhill route."""

        queue = deque([start])
        parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        while queue:
            current = queue.popleft()
            if current != start and self._route_distance.get(current, start_distance) < start_distance:
                while parents[current] != start:
                    parent = parents[current]
                    if parent is None:
                        return None
                    current = parent
                return current
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                candidate = (current[0] + dx, current[1] + dy)
                if (
                    candidate in parents
                    or candidate in occupied
                    or self._route_distance.get(candidate, start_distance + 5) > start_distance + 4
                    or not layout.can_step(
                        observation,
                        {"x": current[0], "y": current[1]},
                        {"x": candidate[0], "y": candidate[1]},
                    )
                ):
                    continue
                parents[candidate] = current
                queue.append(candidate)
        return None

    # Optional: messaging. On your turn, chat receives messages addressed to your player since
    # its previous turn. Return messages with a recipient and text, or nothing to stay silent.
    # Use None as the recipient to broadcast. Every message is recorded and shown in replays.
    #
    # def chat(self, inbox: list[dict]) -> list[dict] | None:
    #     ...
