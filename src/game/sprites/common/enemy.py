from __future__ import annotations
from src.core import *
from .entity import Entity
from abc import abstractmethod

class Enemy(Entity):
    def __init__(self, scene: MainScene, hp: int, pos: Vec) -> None:
        self.image = pygame.transform.rotate(Image.get("test"), 180)
        super().__init__(scene, "DEFAULT", RectHitbox(Vec(pos), self.image.width, self.image.height), hp)
        self.scene = scene
        self.killed = False
        self.damaged_timer = Timer(0.10)
        self.damaged_timer.has_been_done = True
        # TODO: add notice range, forget range

    def update(self, dt: float) -> None:
        self.update_movement(dt)
        self.update_attack(dt)
        self.update_position(dt)
        if self.hp <= 0:
            self.kill()
            return

    @abstractmethod
    def update_movement(self, dt: float):
        # Losing ~99.9% of the velocity after 1 second
        # k = -ln(1 - 0.999) = ~6.9
        self.apply_force(-self.vel * 6.9)

    def update_attack(self, dt: float):
        pass

    def kill(self):
        if not self.killed:
            super().kill()
            self.killed = True

    def get_player_direction(self) -> float:
        return atan2(self.scene.player.pos.y - self.pos.y, self.scene.player.pos.x - self.pos.x)

    def get_player_distance(self) -> float:
        return self.scene.player.pos.distance_to(self.pos)

    def is_near_player(self) -> bool:
        playerhash = self.scene.spacial_hash_key(self.scene.player.pos)
        selfhash = self.scene.spacial_hash_key(self.pos)
        if abs(playerhash.x - selfhash.x) <= 1 and abs(playerhash.y - selfhash.y) <= 1:
            return True
        return False

    def is_colliding_player(self) -> bool:
        if self.is_near_player() and self.hitbox.is_colliding(self.scene.player.hitbox):
            return True
        return False

    def take_damage(self, dmg: int) -> int:
        self.damaged_timer.reset()
        if Debug.on("dmg_message"):
            Log.debug(f"Enemy took {dmg} damage, HP: {self.hp} -> {max(self.hp - dmg, 0)}")
        return super().take_damage(dmg)

    def draw(self, target: pygame.Surface) -> None:
        dmgtint = pygame.Surface(self.image.get_size()).convert_alpha()
        dmgtint.fill((200, 0, 0))
        # TODO: hp bars should probably be a thing (some sprite?)
        if not self.damaged_timer.done:
            tinted_image = self.image.copy()
            tinted_image.blit(dmgtint, (0, 0), special_flags=BLEND_RGBA_MULT)
            self.draw_centered(target, tinted_image)
        else:
            self.draw_centered(target, self.image)
