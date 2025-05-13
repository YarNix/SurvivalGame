import os
from typing import Callable, NamedTuple
import pygame as pg
from enum import IntEnum
from SurvivalGame.components.abstract import PhysicComponent, SpriteComponent
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.entity import Enemy
from SurvivalGame.components.map import TmxMap
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.const import *
from SurvivalGame.typing import *
import random
import pickle
from typing import TypeVar

pg.init()
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Typing
class Action(IntEnum):
    N = 0
    S = 1
    W = 3
    E = 4
    NW = 5
    NE = 6
    SW = 7
    SE = 8
class State(NamedTuple):
    tile: Point
    goal: Point
GTable = dict[Action, float]
T = TypeVar('T')
ACTION_TO_DIRECTION = {
    Action.N: (0, -1),
    Action.S: (0, 1),
    Action.W: (-1, 0),
    Action.E: (1, 0),
    Action.NW: (-1, -1),
    Action.NE: (1, -1),
    Action.SW: (-1, 1),
    Action.SE: (1, 1)
}
# Environment settings
map = TmxMap(join(PT_MAP, "map.tmx"))
render = LayeredRender(2)
for spr, layer in map.map_renders:
    render.add(spr, layer)
ACTIONS = list(Action(value) for value in Action._value2member_map_)
agent = Enemy(skin="Enemy 0", speed=map.tilewidth, spawn=(0, 0))
agent.add_component(CameraComponent, render)
render.add(agent.get_component(SpriteComponent), LayerId.OBJECT)
agent_physic = agent.get_component(PhysicComponent)
map.collide_grid.add(agent)
def update_agent_pos(tile: Point):
    map.collide_grid.remove(agent)
    pos = ((tile[0] + 0.5) * map.tilewidth, (tile[1] + 0.5) * map.tileheight)
    agent.get_component(SpriteComponent).rect.center = pos
    map.collide_grid.add(agent)
    return pos
def get_agent_pos():
    return agent.get_component(SpriteComponent).rect.center
running = True
def update_screen():
    global running
    if len(pg.event.get(pg.QUIT)):
        running = False
        pg.quit()
    else:
        pg.event.get()
        render.render(screen)
        pg.display.update()
# Q-learning parameters
alpha = 0.1        # learning rate
gamma = 0.9        # discount factor
epsilon = 0.2      # exploration rate
episodes = 500

# Initialize Q-table
Q: dict[State, GTable] = {}  # Q[(state, goal)][action] = value

def get_state(pos):
    return pos

def get_actions(pos):
    return ACTIONS

def step(state: State, action: Action) -> tuple[State, float]:
    pos = update_agent_pos(state.tile)
    agent_physic.direction.update(ACTION_TO_DIRECTION[action])
    agent_physic.direction.normalize_ip()
    agent.update(collide_grid = map.collide_grid, dt = 1.0)
    post_pos = get_agent_pos()
    post_tile = (post_pos[0] // map.tilewidth, post_pos[1] // map.tileheight)
    if post_tile == state.goal:
        reward = 10
    elif pg.Vector2(post_pos).distance_to(pos) < map.tilewidth:
        post_tile = state.tile
        reward = -2 # high penalize for remaning in the same tile
    else:
        reward = -1
    #print("rewarding", reward)
    return (State(post_tile, state.goal), reward)

def choose_action(state: State):
    if random.random() < epsilon:
        return random.choice(ACTIONS)
    g_table = Q.get(state, {})
    return max(ACTIONS, key=lambda a: g_table.get(a, 0.0))

def run_episode(state: State, reached_goal: Callable[[State], bool], scale: float):
    MAX_STEPS = int(map.mapwidth * map.mapheight * len(ACTIONS) * scale)
    for nstep in range(MAX_STEPS):
        # Table of rewards
        g_table = Q.setdefault(state, {})
        action = choose_action(state)
        #print("Walking", action._name_, "from", state.tile, end=" ")
        next_state, reward = step(state, action)
        old_q = g_table.get(action, 0)
        future_q = max(Q.get(next_state, {}).values(), default=0)
        # G_t+1 = Q_t + (R_t+1 + G * )
        g_table[action] = old_q + alpha * (reward + gamma * future_q - old_q)
        state = next_state
        if reached_goal(state):
            return True
        if nstep == (MAX_STEPS / 2) and running:
            update_screen()
    return False

SAVE_PROGESS_PATH = 'training.pkl'
SAVE_PATH = 'qtable.pkl'
def save_progress(**kwarg):
    with open(SAVE_PROGESS_PATH, "wb") as f:
        pickle.dump(kwarg, f)

def load_progress() -> dict:
    if os.path.exists(SAVE_PROGESS_PATH):
        print('Resume training from', SAVE_PROGESS_PATH)
        with open(SAVE_PROGESS_PATH, "rb") as f:
            return pickle.load(f)
    return {}

# Load data
session_data = load_progress()
start_x = session_data.get("goal_x", 0)
start_y = session_data.get("goal_y", 0)
start_ep = session_data.get("ep", 0)
Q.update(session_data.get("q_table", {}))
def get_scale(tile):
    pos = ((tile[0] + 0.5) * map.tilewidth, (tile[1] + 0.5) * map.tileheight)
    if (agent.get_component(SpriteComponent).rect.move_to(center=pos).collidelist(map.collisions) >= 0):
        return 1.0
    else:
        return 2.0
# Training loop
scale: float | None = session_data.get('scale', None)
for goal_x in range(start_x, map.mapwidth):
    for goal_y in range(start_y, map.mapheight):
        goaltile = goal_x, goal_y
        if scale is None:
            scale = get_scale((goal_x, goal_y))
        for ep in range(start_ep, episodes):
            try:
                spawn = random.choice(map.markers.get('Enemy', []))
                spawntile = (spawn[0] // map.tilewidth, spawn[1] // map.tileheight)
                if ep % 100 == 0:
                    print("Starting episode", ep, "of position", goaltile)
                if not run_episode(State(spawntile, goaltile), lambda s: s.tile == goaltile, scale):
                    print("The posisition", goaltile, "was unreachable. Futher episodes will be shorter.")
                    scale = scale / 10
                    if scale < 1e-5:
                        break
                elif running:
                    update_screen()
            except Exception as ex:
                ep = min(0, ep - 1)
                print(ex)
                running = False
            if not running:
                save_progress(goal_x=goal_x, goal_y=goal_y, ep=ep, q_table=Q, scale=scale)
                print("Training paused. Progress saved.")
                exit()
        scale = None
        start_ep = 0
        print("Finished running for", goaltile)
    start_y = 0

# Save
with open(SAVE_PATH, 'wb') as f:
    pickle.dump(Q, f)

if os.path.exists(SAVE_PROGESS_PATH):
        os.remove(SAVE_PROGESS_PATH)
pg.quit()