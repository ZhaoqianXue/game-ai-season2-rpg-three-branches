"""Ten villagers with stable, recognizable jobs around the village."""

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
        ("repair_bench", 0, "sweep"),
        ("hearth", 0, "laugh"),
        ("pump", 0, "shrug"),
        ("bell", 0, "startle"),
        ("board", 0, "point"),
    )

    def reset(self, seed: int, observation: ThreeBranchesObservation) -> None:
        """Choose one job from the stable player number."""

        player_number = int(me.player_id(observation).rsplit("_", 1)[1])
        self._job = self._JOBS[(player_number - 1) % len(self._JOBS)]

    def act(self, observation: ThreeBranchesObservation) -> ThreeBranchesAction:
        """Choose one simple order from current sight and standing village knowledge."""

        heading = me.heading(observation)
        here = me.position(observation)
        job_type, job_index, job_emote = self._job
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

        matching_props = [prop for prop in props.all(observation) if prop["type"] == job_type]
        target = matching_props[job_index % len(matching_props)] if matching_props else None
        usable = props.usable(observation)
        if target is not None and usable is not None and usable["id"] == target["id"]:
            return action.stand(heading, "use")
        if target is not None:
            destination = _cell_centre(target["cell"])
            return action.walk(geometry.heading_to(here, destination), 1.0, expression)
        return action.walk(heading, 0.0, expression)

    # Optional: messaging. On your turn, chat receives messages addressed to your player since
    # its previous turn. Return messages with a recipient and text, or nothing to stay silent.
    # Use None as the recipient to broadcast. Every message is recorded and shown in replays.
    #
    # def chat(self, inbox: list[dict]) -> list[dict] | None:
    #     ...
