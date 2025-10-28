from __future__ import annotations
from src.core import *
from src.game.sprites.common import Enemy

class BasicEnemy(Enemy):
    def __init__(self, scene: MainScene, pos: Vec) -> None:
        super().__init__(scene, 25, pos)
        self.damage_cooldown = Timer(1)

    def update_movement(self, dt: float) -> None:
        self.apply_force(1000 * Vec(1, 0).rotate(degrees(self.get_player_direction())))
        super().update_movement(dt)

    def update_attack(self, dt: float) -> None:
        if self.is_colliding_player() and self.damage_cooldown.done:
            self.scene.player.apply_impulse((self.pos - self.scene.player.pos).normalize())
            self.scene.player.take_damage(10)
            self.damage_cooldown.reset()
