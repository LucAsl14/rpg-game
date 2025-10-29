from __future__ import annotations
from src.core import *
from src.game.sprites.common import *

class Waterball(Spell):
    def __init__(self, scene: MainScene) -> None:
        super().__init__(scene)
        self.set_charge_time(1.5)

        player_pos = self.get(self.scene.player, "pos")
        projectile = self.add_action("create", WaterProjectile, self.scene.player, player_pos)
        self.add_action("charge", projectile)
        self.add_action("call", projectile, "release", self["initial_mouse_pos"])

# NOTE: explosion is done inside the WaterProjectile class as it is something
# the projectile does of its own accord, not something the spell does. This is
# NOT the case for charging, as a waterball can very well be summoned without
# having been charged first. The spell MAY control the explosion if it is part
# of the functionality of the spell (i.e. the spellcaster MAKES the ball
# explode), and/or if there are situations where ball may not explode if it did
# not come from a spell.

# This is just a decision made somewhat arbitrarily, if you think the charging
# behavior of the water projectile would never be decoupled from the projectile
# itself, then it would make sense to move the charging behavior entirely to
# within the WaterProjectile class.

class WaterProjectile(Projectile):
    def __init__(self, scene: MainScene, master: Entity, pos: Vec) -> None:
        super().__init__(scene, master, pos, 1, 5, 5, 20)
        self.set_kill_on_collision(True)
        self.set_no_collision(True)
        self.radius = 0
        self.exploding = False
        self.exploding_timer = Timer(0.05)

    def update(self, dt: float) -> None:
        if self.exploding:
            self.radius = self.rad + 100 * self.exploding_timer.progress
            if self.exploding_timer.done:
                self.hitbox.expand(6)
                for entity in self.get_colliding_entities():
                    entity.take_damage(self.damage, "water_explosion")
                super().kill()
            return

        super().update(dt)

    def charge(self, progress: float) -> None:
        self.pos = self.master.pos.copy()
        self.radius = self.rad * progress

    def release(self, mouse_pos: Vec) -> None:
        self.set_no_collision(False)
        self.radius = self.rad
        self.apply_impulse((mouse_pos - self.pos).normalize() * 400)

    def draw(self, target: pygame.Surface) -> None:
        pygame.draw.circle(target, WATER, self.screen_pos, self.radius)

    def kill(self) -> None:
        if not self.exploding:
            self.exploding = True
            self.exploding_timer.reset()
        self.apply_impulse(-self.vel)
