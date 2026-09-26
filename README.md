# Days at Three Branches agent

## Season 2 design

**Design goal.** Make the ten villagers read as one coherent settlement by giving each villager a stable job, workplace, and social mannerism instead of having every copy perform the same routine.

**Design reflection.** I considered a shared utility system and random wandering, but chose deterministic roles derived from each stable player ID because the agents cannot share memory and the result is easier to recognize in a replay. Five villagers tend separate plots while the others work at the repair bench, hearth, pump, bell, and board; they use their assigned prop when in reach and show role-specific emotes around people. After Season 1, I replaced the fixed-emote-only behavior with persistent jobs and distinct destinations so the differences affect what villagers do, not only how they look. The tradeoff is that the direct movement rule is simple and can be less natural around obstacles than a full path planner.

**Rating prompt.** How clearly did the villagers appear to have distinct jobs that fit together as one village?

## AI-use disclosure

I used OpenAI Codex to inspect the course template and helper APIs, implement and review the role-assignment logic in `agent.py`, and run the local checks. I verified the result with `python -m sandbox test` (94 passed), `python -m sandbox eval --parameter seat_plan=cast_10` (five episodes, mean 100.00), and `git diff --check`. The useful part of the process was turning a broad goal such as “make the village coherent” into small observable rules; the main limitation is that automated scoring confirms reliability, not whether the routines look convincing to a human viewer.

Edit `agent.py` to give every one of your villagers a routine. The platform runs a separate `Agent` instance for each NPC, so instances do not share variables or memory. The supplied `sandbox/` directory contains the local runner, types, and village helpers. Leave it unchanged, and leave `requirements.in` and `requirements.txt` alone: the pinned packages match the server.

Start with the [Getting Started guide](https://vox-deorum.github.io/game-sandbox/students/getting-started/). Then run these commands from this folder:

```console
python -m sandbox watch  # watch your villagers and the scripted visitor
python -m sandbox test   # run the checks
python -m sandbox eval   # run repeatable automated days
```

## Files you will use

| Path | Purpose |
| --- | --- |
| `agent.py` | Your `Agent` implementation and starter TODOs. |
| `environment.md` | Rules, helpers, observations, and local commands. |
| `manifest.json` | Tells Game Sandbox where the agent class lives. |
| `season.json` | Optional local season settings downloaded from My Submissions. |
| `tests/` | Checks your submission should pass. |
| `sandbox/` | Local game, helpers, and types. Do not edit it. |
| `requirements.txt` | Exact Python package versions used by the server. |
| `requirements-dev.txt` | Test dependencies. |
| `.env.example` | Example local LLM settings. |

The starter shows `action.walk`, `action.stand`, an emote, and `use`. Read [`environment.md`](environment.md) before changing it. Begin with one behavior that you can recognize in `watch`, then make it more responsive to the people and props it sees.

Chat is optional. If you add `chat(self, inbox)` to your agent, send and receive raw message dictionaries that use canonical player IDs such as `"player_0"` and `"player_1"`. For example, return `[{"to": "player_0", "text": "Hello."}]` to send a direct message. The village helpers do not include a chat namespace. Read [`environment.md`](environment.md#chat-with-other-agents) for the inbox format, broadcasts, and delivery timing.

In `watch` and `eval`, your `Agent` controls the whole cast, and `scripted_visitor` controls the visitor. The `naive` built-in is the simple baseline for the cast. When you are ready to submit, follow the [submitting guide](https://vox-deorum.github.io/game-sandbox/students/submitting/).

## Optional LLM API

If your instructor enables model calls, follow [Using the LLM API](llm.md). Copy `.env.example` to `.env`, add the endpoint and key, and never commit either secret.

Test the connection with:

```console
python -m sandbox llm
```
