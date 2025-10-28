from __future__ import annotations
from src.core import *
from src.game.sprites.common import *

class Fireball(Spell):
    def __init__(self, scene: MainScene) -> None:
        super().__init__(scene)
        self.set_charge_time(0.5)

        player_pos = self.get(self.scene.player, "pos")
        projectile = self.add_action("create", FireProjectile, self.scene.player, player_pos)
        self.add_action("charge", projectile)
        self.add_action("call", projectile, "release", self["initial_mouse_pos"])

class FireProjectile(Projectile):
    def __init__(self, scene: MainScene, master: Entity, pos: Vec) -> None:
        super().__init__(scene, master, pos, 1, 10, 5, 10)
        self.set_kill_on_collision(True)
        self.radius = 0

    def charge(self, progress: float) -> None:
        self.set_solidness(0.0)
        self.radius = self.rad * progress

    def release(self, mouse_pos: Vec) -> None:
        self.radius = self.rad
        self.set_solidness(1.0)
        self.apply_impulse((mouse_pos - self.pos).normalize() * 800)

    def draw(self, target: pygame.Surface) -> None:
        pygame.draw.circle(target, FIRE, self.screen_pos, self.radius)
