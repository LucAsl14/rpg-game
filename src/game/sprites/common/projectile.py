from __future__ import annotations
from src.core import *
from .entity import Entity

class Projectile(Entity):
    def __init__(self, scene: MainScene, master: Entity, pos: Vec, hp: int, lifetime: int) -> None:
        super().__init__(scene, "DEFAULT", PolygonalHitbox.from_rect(pos, 40, 40), hp)
        # TODO: Add damage groups (projectiles from enemies don't damage other enemies, etc.)
        self.set_collision_ignore_entities(master)
        self.lifetime = lifetime
        self.kill_timer = Timer(lifetime)
        self._kill_on_collision = False
        self._self_damage = 0
        self._collide_on_hitbox_enter = True
        # Used to store entities that the projectile collides with
        # This is used to prevent consecutive collisions with the same entity
        self.colliding_entities = set()

    def update(self, dt: float) -> None:
        super().update_position(dt)

        current_colliding = set(self.get_colliding_entities())
        active_collisions = current_colliding - self.colliding_entities \
            if self._collide_on_hitbox_enter else current_colliding

        for entity in active_collisions:
            entity.take_damage(10) # TODO: Fix this hardcoded damage
            self.take_damage(self._self_damage)
            if self._kill_on_collision:
                self.kill()
                return
            break # Only collide with the first entity

        self.colliding_entities = current_colliding

        if self.kill_timer.done:
            self.kill()

    def set_kill_on_collision(self, yes: bool) -> None:
        """Set the projectile to kill itself on collision with an entity.
        (default: False)"""
        self._kill_on_collision = yes

    def set_self_damage_on_collision(self, damage: int) -> None:
        """Set how much damage is dealt to the projectile on collision.
        (default: 0)"""
        self._self_damage = damage

    def set_collide_on_hitbox_enter(self, yes: bool) -> None:
        """Set the projectile to trigger a collision only when its hitbox
        first enters another entity's hitbox. (default: True)"""
        self._collide_on_hitbox_enter = yes
