from __future__ import annotations
from src.core import *
from src.game.sprites.common import *

class WallOfLight(Spell):
    def __init__(self, scene: MainScene, radius: int) -> None:
        super().__init__(scene)

        preview = self.add_action("create", WallOfLightSegmentPreview, radius)
        first_segment = self.add_action("create", WallOfLightSegment, scene.world_mouse_pos, radius, 50, self)
        self.add_action("call_until_true", self, "create_wall", radius, first_segment)
        self.add_action("kill", preview)

        self.current_segment: WallOfLightSegment
        self.segment_count = 1

    # NOTE: Any FutureReturnValue passed through an `add_action` will be
    # automatically converted to its value when the action is executed.
    # So `first_segment` here is a real WallOfLightSegment instance.
    def create_wall(self, radius: int, first_segment: WallOfLightSegment) -> bool:
        if self.segment_count == 1:
            self.current_segment = first_segment

        diff = self.scene.world_mouse_pos - self.current_segment.pos
        while diff.length() > radius:
            new_pos = self.current_segment.pos + diff.normalize() * radius
            new_segment = WallOfLightSegment(self.scene, new_pos, radius, 50, self, first_segment)
            diff = self.scene.world_mouse_pos - new_pos
            self.scene.add(new_segment)
            self.current_segment = new_segment
            self.segment_count += 1
            if self.segment_count >= 60:
                return True
        return False

# TODO: this never expires currently, fix that
class WallOfLightSegment(Entity):
    def __init__(self,
                 scene: MainScene,
                 pos: Vec,
                 radius: int,
                 hp: int,
                 spell_origin: Optional[WallOfLight]=None,
                 first_segment: Optional[WallOfLightSegment]=None) -> None:
        super().__init__(scene, "DEFAULT", CircleHitbox(pos, radius), hp)
        self.set_movability(0.0) # immovable
        self.set_solidness(0.0) # (does not push out other entities)
        self.set_collision_ignore_classes(WallOfLightSegment)
        self.pos = pos
        self.origin = spell_origin
        self.radius = radius
        self.lifespan_timer = Timer(20)
        self.first_segment = first_segment
        self.killed = False
        self.set_no_collision(True)

    def kill(self) -> None:
        self.killed = True
        super().kill()

    def take_damage(self, dmg: int, source: str = "normal") -> int:
        if self.first_segment is not None:
            return self.first_segment.take_damage(dmg, source)
        return super().take_damage(dmg, source)

    def update(self, dt: float) -> None:
        if self.origin is not None and self.origin.segment_count >= 60:
            self.origin = None
            self.set_no_collision(False)
            self.lifespan_timer.reset()

        if self.first_segment is not None and self.first_segment.killed:
            self.kill()
            return

        if self.lifespan_timer.done and self.origin is None:
            self.kill()
            return

        if self.hp <= 0:
            self.kill()
            return
        super().update_position(dt)

    def draw(self, target: pygame.Surface) -> None:
        trans_surf = pygame.surface.Surface(Vec(self.radius * 2), pygame.SRCALPHA)
        if self.origin is not None:
            pygame.draw.circle(trans_surf, AIR + (160,), Vec(self.radius), self.radius)
        else:
            pygame.draw.circle(trans_surf, LIGHT + (200,), Vec(self.radius), self.radius)
        target.blit(trans_surf, self.screen_pos - Vec(self.radius))

class WallOfLightSegmentPreview(Sprite):
    def __init__(self, scene: Scene, radius) -> None:
        super().__init__(scene, "DEFAULT")
        self.radius = radius

    def update(self, dt: float) -> None:
        self.scene: MainScene # I swear there must be a way around this
        self.pos = self.scene.world_mouse_pos

    def draw(self, target: pygame.Surface) -> None:
        trans_surf = pygame.surface.Surface(Vec(self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(trans_surf, AIR + (160,), Vec(self.radius), self.radius)
        target.blit(trans_surf, self.screen_pos - Vec(self.radius))
