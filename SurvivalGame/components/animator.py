from typing import Protocol
from SurvivalGame.components.abstract import FrameAnimation, PhysicComponent, SpriteComponent, AbstractEntity
from SurvivalGame.components.sprites import SpriteSheetImage
from SurvivalGame.components.state import PlayerStateComponent
from SurvivalGame.const import *
from SurvivalGame.typing import *
import pygame as pg

class SingleKeyFrameAnimation(FrameAnimation):
    def __init__(self, keyframe: str):
        self.keyframe = keyframe
        self.drawn = False
    def step(self, dt):
        if self.drawn:
            return False
        self.drawn = True
        return True
    def restart(self):
        pass
    @property
    def index(self):
        return self.keyframe

class MultiKeyFramesAnimation(FrameAnimation):
    def __init__(self, keyframes: list[KeyFrame]):
        self.keyframes = keyframes
        self.restart()
        # self.elapsed_time = 0.0
        # self.frame_index = 0
        # self.frame_duration = float(keyframes[0][1])
    
    def step(self, dt):
        self.elapsed_time += dt * 1000
        redraw = False
        while self.elapsed_time >= self.frame_duration:
            self.elapsed_time -= self.frame_duration
            self.frame_index += 1
            if self.frame_index >= len(self.keyframes):
                self.frame_index = 0
            redraw = True
        return redraw
    
    def restart(self):
        self.elapsed_time = 0.0
        self.frame_index = 0
        self.frame_duration: float = self.keyframes[0][1]

    @property
    def index(self):
        return self.keyframes[self.frame_index][0]

def create_animation(animation: AnimationData) -> FrameAnimation:
    if not isinstance(animation, list):
        return SingleKeyFrameAnimation(animation)
    else:
        return MultiKeyFramesAnimation(animation)

class BasicAnimator:
    needs_update = True
    update_order = ORD_ANIMATE
    def __init__(self, sheet: SpriteSheetImage, default_state: str | None = None):
        self.sprites = sheet.sprites
        self.states = sheet.states
        try:
            current_state = sheet.states[default_state or next(iter(sheet.states.keys()))]
        except KeyError:
            raise KeyError(f"The state {default_state} does not exist in the sprite sheet.")
        except StopIteration:
            raise ValueError('Missing a default state for the sprite!')
        self._animation = create_animation(current_state)

    def on_attach(self, entity: AbstractEntity):
        sprite = entity.get_component(SpriteComponent, None)
        if sprite is None:
            print('Warning: Animator attached on a spriteless entity!')
            return
        sprite.image = self.sprites[self._animation.index]
        sprite.rect.update(sprite.image.get_frect(center=sprite.rect.center))

    def update(self, entity: AbstractEntity, dt, *_, **__):
        if self._animation.step(dt):
            sprite = entity.get_component(SpriteComponent, None)
            if sprite is None:
                return
            sprite.image = self.sprites[self._animation.index]
            sprite.rect.update(sprite.image.get_frect(center=sprite.rect.center))

    def change_state(self, new_state: str):
        self._animation = create_animation(self.states[new_state])

class PlayerAnimator:
    needs_update = True
    update_order = ORD_ANIMATE
    def __init__(self, player_sprite: SpriteSheetImage):
        REQUIRE_STATES = ['Stand', 'Dead', 'Run']
        self.sprites = player_sprite.sprites
        if any(state for state in REQUIRE_STATES if state not in player_sprite.states):
            raise ValueError(f'Missing states for the {PlayerAnimator.__name__}')
        self.animations = {state: create_animation(data) for state, data in player_sprite.states.items()}
        self.current_state = 'Stand'
        self.flipped = False

    def on_attach(self, entity: AbstractEntity):
        sprite = entity.get_component(SpriteComponent, None)
        if sprite is None:
            print('Warning: Animator attached on a spriteless entity!')
            return
        sprite.image = self.sprites[self.animations[self.current_state].index]
        sprite.rect.update(sprite.image.get_frect(center=sprite.rect.center))

    def update(self, entity: AbstractEntity, dt, *_, **__):
        sprite = entity.get_component(SpriteComponent, None)
        physic = entity.get_component(PhysicComponent, None)
        state = entity.get_component(PlayerStateComponent, None)
        if sprite is None or physic is None or state is None:
            return
        
        redraw = False
        if state.health <= 0:
            if self.current_state != 'Dead':
                self.current_state = 'Dead'
                redraw = True
        else:
            dir_x, dir_y = physic.direction.xy
            if (dir_x, dir_y) != (0, 0):
                if self.current_state != 'Run':
                    self.current_state = 'Run'
                    redraw = True
                if dir_x != 0 and (physic.direction.x < 0) != self.flipped:
                    self.flipped = physic.direction.x < 0
                    redraw = True
            elif self.current_state != 'Stand':
                self.current_state = 'Stand'
                redraw = True
        
        current_ani = self.animations[self.current_state]
        if redraw:
            current_ani.restart() 
        else:
            redraw = current_ani.step(dt)
        
        if redraw:
            new_sprite = self.sprites[current_ani.index]
            if self.flipped:
                new_sprite = pg.transform.flip(new_sprite, True, False)
            sprite.image = new_sprite
            sprite.rect.update(sprite.image.get_frect(center=sprite.rect.center))

class EnemyAnimator:
    needs_update = True
    update_order = ORD_ANIMATE
    def __init__(self, enemy_sprite: SpriteSheetImage) -> None:
        REQUIRE_STATES = ['Dead', 'Hit', 'Run']
        self.sprites = enemy_sprite.sprites
        if any(state for state in REQUIRE_STATES if state not in enemy_sprite.states):
            raise ValueError(f'Missing states for the {type(self).__name__}')
        self.animations = {state: create_animation(data) for state, data in enemy_sprite.states.items()}
        self.current_state = 'Run'
        self.flipped = True

    def on_attach(self, entity: AbstractEntity):
        sprite = entity.get_component(SpriteComponent, None)
        if sprite is None:
            print('Warning: Animator attached on a spriteless entity!')
            return
        sprite.image = self.sprites[self.animations[self.current_state].index]
        sprite.rect.update(sprite.image.get_frect(center=sprite.rect.center))

    def update(self, entity: AbstractEntity, dt, *_, **__):
        sprite = entity.get_component(SpriteComponent, None)
        physic = entity.get_component(PhysicComponent, None)
        if sprite is None or physic is None:
            return
        redraw = False
        dir_x, dir_y = physic.direction.xy
        if dir_x != 0 and (physic.direction.x < 0) != self.flipped:
            self.flipped = physic.direction.x < 0
            redraw = True

        current_ani = self.animations[self.current_state]
        if redraw:
            current_ani.restart() 
        else:
            redraw = current_ani.step(dt)
        
        if redraw:
            new_sprite = self.sprites[current_ani.index]
            if self.flipped:
                new_sprite = pg.transform.flip(new_sprite, True, False)
            sprite.image = new_sprite
            sprite.rect.update(sprite.image.get_frect(center=sprite.rect.center))