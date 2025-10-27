from __future__ import annotations
from src.core import *

from .inventory import Inventory
from .basic_enemy import BasicEnemy
from .waterball_enemy import WaterballEnemy
from .spell_queue import SpellQueue
from src.game.sprites.common import Entity
from .spells.waterball import Waterball
from .spells.fireball import Fireball
from .spells.wall_of_fire import WallOfFire

class Player(Entity):
    def __init__(self, scene: MainScene) -> None:
        size = Vec(Image.get("player").size)
        super().__init__(scene, "DEFAULT", PolygonalHitbox.from_rect(Vec(), size.x, size.y), 100)
        # band-aid fix to scene not considered MainScene
        self.scene = scene

        # inventory
        self.inventory = Inventory(self.scene)
        for _ in range(10):
            self.inventory.add("water")
            self.inventory.add("fire")
            self.inventory.add("earth")
            self.inventory.add("air")
        self.scene.add(self.inventory)

        # spell queue
        self.spell_queue = SpellQueue(self.scene)
        self.scene.add(self.spell_queue)

    def update(self, dt: float) -> None:
        self.update_keys(dt)
        self.update_position(dt)
        self.update_surroundings()
        Debug.add_entry("hp", self.hp)
        Debug.add_entry("pos", self.pos)

    def draw(self, target: pygame.Surface) -> None:
        self.draw_centered(target, Image.get("player"))

    def update_keys(self, dt: float) -> None:
        self.keys = pygame.key.get_pressed()

        # movement keys
        if self.keys[K_w]:
            self.apply_force(Vec(0, -PLAYER_ACC))
        if self.keys[K_s]:
            self.apply_force(Vec(0, PLAYER_ACC))
        if self.keys[K_a]:
            self.apply_force(Vec(-PLAYER_ACC, 0))
        if self.keys[K_d]:
            self.apply_force(Vec(PLAYER_ACC, 0))
        # Losing ~99.9% of the velocity after 1 second
        # k = -ln(1 - 0.999) = ~6.9
        self.apply_force(-self.vel * 6.9)

        # spell keys
        if KEYDOWN in self.game.events:
            match self.game.key_down:
                case pygame.K_j | pygame.K_1:
                    if self.inventory.take("water"):
                        self.spell_queue.push("water")
                case pygame.K_i | pygame.K_2:
                    if self.inventory.take("air"):
                        self.spell_queue.push("air")
                case pygame.K_k | pygame.K_3:
                    if self.inventory.take("earth"):
                        self.spell_queue.push("earth")
                case pygame.K_l | pygame.K_4:
                    if self.inventory.take("fire"):
                        self.spell_queue.push("fire")
                case pygame.K_SPACE:
                    if len(self.spell_queue.queue) and self.spell_queue.queue[-1] != " ":
                        self.spell_queue.push(" ")
                case pygame.K_BACKSPACE:
                    removed = self.spell_queue.remove()
                    if removed != "" and removed != " ":
                        self.inventory.add(removed)

        if self.game.key_down == pygame.K_q:
            self.scene.add(WallOfFire(self.scene))

    def update_surroundings(self) -> None:
        # something something about generating decorations im too lazy
        pass
