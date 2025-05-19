import os
import time
from typing import Callable, NamedTuple
import pandas as pd
import pygame as pg
from SurvivalGame.components.abstract import SpriteComponent
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.entity import Enemy, EnemyType
from SurvivalGame.components.grid import SpatialGrid
from SurvivalGame.components.map import TmxMap
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.physic import BoundingBoxCollider
from SurvivalGame.components.pathfind import Action
from SurvivalGame.const import *
from SurvivalGame.typing import *
import random
import pickle
from typing import TypeVar

# Typing
class State(NamedTuple):
    tile: Point
    goal: Point
GTable = dict[Action, float]
PostQTable = dict[State, Action]
T = TypeVar('T')
# Const
ACTIONS = list(Action(value) for value in Action._value2member_map_)
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
SAVE_PROGESS_PATH = 'training.pkl'
SAVE_PATH = 'qtable.pkl'
# Functions
def tile_to_pos(tile: Point):
    return ((tile[0] + 0.5) * map.tilewidth, (tile[1] + 0.5) * map.tileheight)
def pos_to_tile(pos: Point):
    return (pos[0] // map.tilewidth, pos[1] // map.tileheight)

def update_agent_pos(tile: Point):
    collide_grid.remove(agent)
    pos = tile_to_pos(tile)
    agent.get_component(SpriteComponent).rect.center = pos
    collide_grid.add(agent)
    return pos
def get_agent_pos():
    return agent.get_component(SpriteComponent).rect.center

def update_screen():
    global running
    if len(pg.event.get(pg.QUIT)):
        running = False
    else:
        pg.event.get()
        render.render(screen)
        pg.display.update()

def save_progress(**kwarg):
    with open(SAVE_PROGESS_PATH, "wb") as f:
        pickle.dump(kwarg, f)

def load_progress() -> dict:
    if os.path.exists(SAVE_PROGESS_PATH):
        print('Resume training from', SAVE_PROGESS_PATH)
        with open(SAVE_PROGESS_PATH, "rb") as f:
            return pickle.load(f)
    return {}

def get_time():
    return time.strftime('%H:%M:%S', time.localtime())

# Q-learning parameters
ALPHA = 0.1        # learning rate
GAMMA = 0.9        # discount factor
EPSILON = 0.2      # exploration rate
EPISODES = 1000

# Q-learning functions
def step(state: State, action: Action) -> tuple[State, float]:
    pos = update_agent_pos(state.tile)
    agent_physic.direction.update(ACTION_TO_DIRECTION[action])
    agent_physic.direction.normalize_ip()
    agent.update(collide_grid = collide_grid, dt = 1.0)
    post_pos = get_agent_pos()
    post_tile = pos_to_tile(post_pos)
    if post_tile == state.goal:
        reward = 10
    elif pg.Vector2(post_pos).distance_to(pos) < map.tilewidth:
        post_tile = state.tile
        reward = -5 # high penalize for remaning in the same tile
    else:
        reward = -1
    #print("rewarding", reward)
    return (State(post_tile, state.goal), reward)

def choose_action(state: State):
    if random.random() < EPSILON:
        return random.choice(ACTIONS)
    g_table = Q.get(state, {})
    return max(ACTIONS, key=lambda a: g_table.get(a, 0.0))

def run_episode(state: State, reached_goal: Callable[[State], bool], scale: float):
    MAX_STEPS = int(map.mapwidth * map.mapheight * len(ACTIONS) * scale)
    for nstep in range(MAX_STEPS):
        # Table of rewards
        g_table = Q.setdefault(state, {})
        action = choose_action(state)
        next_state, reward = step(state, action)
        old_q = g_table.get(action, 0)
        future_q = max(Q.get(next_state, {}).values(), default=0)
        g_table[action] = old_q + ALPHA * (reward + GAMMA * future_q - old_q)
        state = next_state
        if reached_goal(state):
            return True
        if nstep % (MAX_STEPS / 4) == (MAX_STEPS - 1) and running:
            update_screen()
    return False

def trim_table():
    spawns = map.markers['Enemy']
    can_reach = set()
    for x in range(map.mapwidth):
        for y in range(map.mapheight):
            reached = set()
            for spawn in spawns:
                spawntile = pos_to_tile(spawn)
                state = State(spawntile, (x, y))
                reached.add(spawntile)
                for _ in range(map.mapwidth * map.mapheight * len(ACTIONS)):
                    best_action: Action | None = POST_Q.get(state)
                    if best_action is None:
                        break
                    dir = ACTION_TO_DIRECTION[best_action]
                    state = State((state.tile[0] + dir[0], state.tile[1] + dir[1]), state.goal)
                    if state.tile in reached:
                        break
                    reached.add(state.tile)
                    if state.tile == state.goal:
                        break
                if state.tile == state.goal:
                    can_reach.add((x, y))
                    break
            else:
                #print((x, y), 'was unreached')
                pass
    print('Reached', len(can_reach), 'tile(s)')
    print('Before trimming', len(POST_Q))
    new_q = {k: v for k, v in POST_Q.items() if k.goal in can_reach}
    POST_Q.clear()
    POST_Q.update(new_q)
    print('After trimming', len(POST_Q))

def q_to_dataframe(post_q: dict[State, Action]):
    data: dict[Point, dict[Point, int]] = {}
    goals = set()
    tiles = set()
    for state, action in post_q.items():
        goal = (int(state.goal[0]), int(state.goal[1]))
        tile = (int(state.tile[0]), int(state.tile[1]))
        goals.add(goal)
        tiles.add(tile)
        data.setdefault(goal, {})[tile] = int(action)
    return pd.DataFrame(data, index=list(tiles), columns=list(goals), dtype=pd.Int16Dtype())
                
def get_scale(tile):
    pos = tile_to_pos(tile)
    if (agent.get_component(SpriteComponent).rect.move_to(center=pos).collidelist(map.collisions) >= 0):
        return 0.5
    else:
        return 1.0

if __name__ == '__main__':
    pg.init()
    running = True
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    map = TmxMap(join(PT_MAP, "map.tmx"))
    collide_grid = SpatialGrid()
    for rect in map.collisions:
        collide_grid.add(rect)
    render = LayeredRender(2.5)
    for spr in map.map_sprites:
        render.add(spr)

    agent = Enemy(type_name=EnemyType.UNKNOWN, skin="Enemy 0", speed=map.tilewidth, spawn=(0, 0))
    agent.add_component(CameraComponent, render)
    render.add(agent.get_component(SpriteComponent))
    agent_physic = agent.get_component(BoundingBoxCollider)
    agent_physic.clip = False
    collide_grid.add(agent)

    # Q[(state, goal)][action] = value
    Q: dict[State, GTable] = {}
    POST_Q: PostQTable = {}

    session_data = load_progress()
    last_x = session_data.get("x", 0)
    last_y = session_data.get("y", 0)
    last_ep = session_data.get("ep", 0)
    Q.update(session_data.get("q_table", {}))
    POST_Q.update(session_data.get('post_q', {}))

    # Training loop
    scale: float | None = session_data.get('scale', None)
    for goal_x in range(last_x, map.mapwidth):
        for goal_y in range(last_y, map.mapheight):
            goal_tile = goal_x, goal_y
            if last_ep == 0:
                Q.clear()
            if scale is None:
                scale = get_scale((goal_x, goal_y))
            for ep in range(last_ep, EPISODES):
                try:
                    spawn = random.choice(map.markers.get('Enemy', []))
                    spawntile = pos_to_tile(spawn)
                    if ep % 200 == 0:
                        
                        print(get_time(), "Starting episode", ep, "of position", goal_tile)
                    if not run_episode(State(spawntile, goal_tile), lambda s: s.tile == goal_tile, scale):
                        print(get_time(), "The posisition", goal_tile, "was unreachable. Futher episodes will be shorter.")
                        scale = scale / 10
                        if scale < 1e-5:
                            break
                    elif running:
                        update_screen()
                except KeyboardInterrupt:
                    pg.quit()
                    exit(1)
                except Exception as ex:
                    ep = min(0, ep - 1)
                    print(ex)
                    running = False
                if not running:
                    save_progress(x=goal_x, y=goal_y, ep=ep, q_table=Q, scale=scale, post_q=POST_Q)
                    print("Training paused. Progress saved.")
                    pg.quit()
                    exit()
            for state, gtable in Q.items():
                best_action = max(gtable, key=gtable.__getitem__, default=None)
                if best_action:
                    POST_Q.setdefault(state, best_action)
            scale = None
            last_ep = 0
            print("Finished running for", goal_tile)
        last_y = 0
    
    # Save
    with open(SAVE_PATH, 'wb') as f:
        pickle.dump(q_to_dataframe(POST_Q), f)

    if os.path.exists(SAVE_PROGESS_PATH):
        os.remove(SAVE_PROGESS_PATH)
    pg.quit()