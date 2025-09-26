from __future__ import annotations
from src.core import *
from src.game.sprites.common import *

SEGMENT_RAD = 15

class WallOfFire(Spell):
    def __init__(self, scene: MainScene) -> None:
        super().__init__(scene)

        preview = self.add_action("create", WallOfFireSegmentPreview)
        first_segment = self.add_action("create", WallOfFireSegment, scene.world_mouse_pos)
        self.add_action("call_until_true", self, "create_wall", first_segment)
        self.add_action("kill", preview)

        self.current_segment: WallOfFireSegment
        self.segment_count = 1

    # NOTE: Any FutureReturnValue passed through an `add_action` will be
    # automatically converted to its value when the action is executed.
    # So `first_segment` here is a real WallOfFireSegment instance.
    def create_wall(self, first_segment: WallOfFireSegment) -> bool:
        if self.segment_count == 1:
            self.current_segment = first_segment

        diff = self.scene.world_mouse_pos - self.current_segment.pos
        while diff.length() > SEGMENT_RAD:
            new_pos = self.current_segment.pos + diff.normalize() * SEGMENT_RAD
            new_segment = WallOfFireSegment(self.scene, new_pos)
            diff = self.scene.world_mouse_pos - new_pos
            self.scene.add(new_segment)
            self.current_segment = new_segment
            self.segment_count += 1
            if self.segment_count >= 20:
                return True
        return False

class WallOfFireSegment(Entity):
    # NOTE: This could just become a reusable fire area effect
    def __init__(self, scene: MainScene, pos: Vec) -> None:
        super().__init__(scene, "GROUND", CircleHitbox(pos, 15), 1)
        self.set_movability(0.0) # immovable
        self.set_solidness(0.0) # (does not push out other entities)
        self.set_collision_ignore_classes(WallOfFireSegment)
        self.pos = pos
        self.damage_timer = LoopTimer(0.2)

    def update(self, dt: float) -> None:
        if self.damage_timer.done:
            for entity in self.get_colliding_entities():
                entity.take_damage(1)

        super().update_position(dt)

    def draw(self, target: pygame.Surface) -> None:
        pygame.draw.circle(target, FIRE, self.screen_pos, SEGMENT_RAD)

class WallOfFireSegmentPreview(Sprite):
    def __init__(self, scene: Scene) -> None:
        super().__init__(scene, "DEFAULT")

    def update(self, dt: float) -> None:
        self.scene: MainScene # I swear there must be a way around this
        self.pos = self.scene.world_mouse_pos

    def draw(self, target: pygame.Surface) -> None:
        target.blit(circle_surface(SEGMENT_RAD, FIRE + (100,)), self.screen_pos - Vec(SEGMENT_RAD))
