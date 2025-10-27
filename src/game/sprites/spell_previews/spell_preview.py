from __future__ import annotations
from src.core import *

class SpellPreview(Sprite):
    def __init__(self, scene: MainScene, spell: Callable, cooldown: float, args: list) -> None:
        super().__init__(scene, "DEFAULT")
        self.scene = scene
        self.spell = spell
        self.cooldown = cooldown
        self.args = args.copy()

    def update(self, dt: float) -> None:
            if MOUSEBUTTONDOWN in self.game.events:
                self.trigger_spell()
                self.kill()

    def draw(self, target: pygame.Surface) -> None:
        pass

    def trigger_spell(self) -> None:
        # Only spend the spell from the queue, but don't spawn the actual spell
        self.scene.player.spell_queue.spend_top_spell()
        # Removed spell spawning code
        self.scene.add(self.spell(self.scene, *self.args))
