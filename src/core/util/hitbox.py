from __future__ import annotations
from .vector import Vec
from typing import List
from math import radians, cos, sin, pi
from abc import ABC as AbstractClass, abstractmethod
import pygame

class Hitbox(AbstractClass):
    def __init__(self, center: Vec, size: Vec) -> None:
        self.center = center
        self.size = size
        self.rotation = 0

    def set_position(self, center: Vec) -> None:
        """Set the center of the hitbox to a new position."""
        self.center = center

    def set_rotation(self, angle: float) -> None:
        self.rotation = angle
        self.apply_rotation(angle)

    def apply_rotation(self, angle: float) -> None:
        # No default implementation
        pass

    @abstractmethod
    def expand(self, factor: float) -> None:
        """Expand the size of the hitbox by a factor."""
        pass

    @abstractmethod
    def is_colliding(self, other: Hitbox) -> bool:
        """Check if this hitbox is colliding with another hitbox."""
        pass

    @abstractmethod
    def draw(self, target: pygame.Surface, camera_pos: Vec) -> None:
        """Draw the hitbox for debugging purposes."""
        pass

class SimpleCircleHitbox(Hitbox):
    # Forces all other hitboxes to performance approx. circle-circle collision
    def __init__(self, center: Vec, rad: int) -> None:
        super().__init__(center, Vec(rad * 2, rad * 2))
        self.radius = rad

    def expand(self, factor: float) -> None:
        self.radius *= factor
        self.size = Vec(self.radius * 2, self.radius * 2)

    def is_colliding(self, other: Hitbox) -> bool:
        """Approximate circle-circle collision detection regardless of the type
        of the other Hitbox."""
        if isinstance(other, (SimpleCircleHitbox, CircleHitbox)):
            dist = self.center.distance_to(other.center)
            return dist < self.radius + other.radius
        elif isinstance(other, (RectHitbox, PolygonalHitbox)):
            dist = self.center.distance_to(other.center)
            return dist < self.radius + (other.size.x + other.size.y) / 2
        else:
            raise TypeError(f"Uhhhhh... How did we get here?")

    def draw(self, target: pygame.Surface, camera_pos: Vec) -> None:
        pygame.draw.circle(target, (255, 0, 0), self.center - camera_pos, self.radius, 2)

class CircleHitbox(Hitbox):
    # Actually performs proper circle-anything collision
    def __init__(self, center: Vec, rad: int) -> None:
        super().__init__(center, Vec(rad * 2, rad * 2))
        self.radius = rad

    def expand(self, factor: float) -> None:
        self.radius *= factor
        self.size = Vec(self.radius * 2, self.radius * 2)

    def is_colliding(self, other: Hitbox) -> bool:
        if isinstance(other, (SimpleCircleHitbox, CircleHitbox)):
            dist = self.center.distance_to(other.center)
            return dist < self.radius + other.radius
        elif isinstance(other, RectHitbox):
            return self._is_colliding_with_rect(other)
        elif isinstance(other, PolygonalHitbox):
            return self._is_colliding_with_polygon(other)
        else:
            raise TypeError(f"Uhhhhh... How did we get here?")

    def _is_colliding_with_rect(self, other: RectHitbox) -> bool:
        # The idea here is to find the closest point on the rectangle to the circle's center
        closest_x = max(other.left, min(self.center.x, other.right))
        closest_y = max(other.top, min(self.center.y, other.bottom))
        distance_sqr = self.center.distance_squared_to(Vec(closest_x, closest_y))
        return distance_sqr < self.radius * self.radius

    def _is_colliding_with_polygon(self, other: PolygonalHitbox) -> bool:
        # Check if circle center is inside polygon (assuming the polygon is defined counter-clockwise)
        inside = True
        poly = other.get_hitbox()
        for i in range(len(poly)):
            point1 = poly[i]
            point2 = poly[(i+1) % len(poly)]
            edge = point2 - point1
            to_center = self.center - point1
            # the cross product is positive if the point is to the left of the edge
            cross = edge.x * to_center.y - edge.y * to_center.x
            if cross < 0:
                inside = False
                break
        if inside:
            # if the center is to the left of all edges, it's inside
            return True

        # Check distance to each edge
        for i in range(len(poly)):
            point1 = poly[i]
            point2 = poly[(i+1) % len(poly)]
            edge = point2 - point1
            edge_length_sqr = edge.length_squared()

            # standard projection formula
            t = max(0, min(1, (self.center - point1).dot(edge) / edge_length_sqr))
            projection = point1 + edge * t

            distance_sqr = self.center.distance_squared_to(projection)
            if distance_sqr < self.radius * self.radius:
                return True
        return False

    def draw(self, target: pygame.Surface, camera_pos: Vec) -> None:
        pygame.draw.circle(target, (255, 0, 0), self.center - camera_pos, self.radius, 2)

class RectHitbox(Hitbox):
    def __init__(self, center: Vec, width: float, height: float) -> None:
        super().__init__(center, Vec(width, height))
        self.left = center.x - width / 2
        self.top = center.y - height / 2
        self.right = center.x + width / 2
        self.bottom = center.y + height / 2
        self.width = width
        self.height = height

    def expand(self, factor: float) -> None:
        self.width *= factor
        self.height *= factor
        self.size = Vec(self.width, self.height)
        self.left = self.center.x - self.width / 2
        self.top = self.center.y - self.height / 2
        self.right = self.center.x + self.width / 2
        self.bottom = self.center.y + self.height / 2

    def set_position(self, center: Vec) -> None:
        super().set_position(center)
        # Remember to update rectangle sides!
        self.left = center.x - self.size.x / 2
        self.top = center.y - self.size.y / 2
        self.right = center.x + self.size.x / 2
        self.bottom = center.y + self.size.y / 2

    def is_colliding(self, other: Hitbox) -> bool:
        if isinstance(other, SimpleCircleHitbox):
            return other.is_colliding(self)
        elif isinstance(other, CircleHitbox):
            return other._is_colliding_with_rect(self)
        elif isinstance(other, RectHitbox):
            return self._is_colliding_with_rect(other)
        elif isinstance(other, PolygonalHitbox):
            return self._is_colliding_with_polygon(other)
        else:
            raise TypeError(f"Uhhhhh... How did we get here?")

    def _is_colliding_with_rect(self, other: RectHitbox) -> bool:
        return not (self.left > other.right or self.right < other.left or
                    self.top > other.bottom or self.bottom < other.top)

    def _is_colliding_with_polygon(self, other: PolygonalHitbox) -> bool:
        poly = PolygonalHitbox.from_rect(self.center, self.width, self.height)
        return other.is_colliding(poly)

    def draw(self, target: pygame.Surface, camera_pos: Vec) -> None:
        pygame.draw.rect(target, (255, 0, 0), (self.left - camera_pos.x, self.top - camera_pos.y, self.size.x, self.size.y), 2)

class PolygonalHitbox(Hitbox):
    """
    A polygonal shape that detects collisions with other polygonal shapes
    """
    # hmm this description is kinda bad

    @classmethod
    def from_rect(cls, center: Vec, dx: float, dy: float) -> Hitbox:
        """
        Creates a Hitbox from a rectangle with the given center and size.
        The rectangle is centered at the given center point.
        """
        return cls(center, [
            Vec(-dx/2, -dy/2),
            Vec(-dx/2,  dy/2),
            Vec( dx/2,  dy/2),
            Vec( dx/2, -dy/2),
        ])

    @classmethod
    def from_circle(cls, center: Vec, rad: float) -> Hitbox:
        """
        Creates a Hitbox from a circle with the given center and radius.
        The circle is centered at the given center point.
        """
        points = []
        for i in range(6):
            points.append(Vec(rad * cos(2 * pi * i / 6), rad * sin(2 * pi * i / 6)))
        return cls(center, points)

    def __init__(self, center: Vec, vertices: List[Vec]) -> None:
        super().__init__(center, Vec(
            max((abs(v.x) for v in vertices), default=0) * 2,
            max((abs(v.y) for v in vertices), default=0) * 2
        ))
        # vertices in this case should be distance from 0 i think?
        self.center = center
        self.original_vertices = vertices
        self.vertices = vertices
        self.angle_rad = 0

    def apply_rotation(self, angle: float) -> None:
        self.angle_rad = radians(angle)
        self.__update_rotation()

    def rotate(self, angle: float) -> None:
        self.angle += angle
        self.set_rotation(self.angle)

    def translate(self, translation: Vec) -> None:
        """ This does not move the center """
        translated = []
        for p in self.original_vertices:
            trans_x = p.x + translation.x
            trans_y = p.y + translation.y
            translated.append(Vec(trans_x, trans_y))
        self.original_vertices = translated

    def __update_rotation(self) -> None:
        cos_a = cos(self.angle_rad)
        sin_a = sin(self.angle_rad)
        rotated = []

        for p in self.original_vertices:
            rotated_x = p.x * cos_a + p.y * sin_a
            rotated_y = p.x * sin_a - p.y * cos_a
            rotated.append(Vec(rotated_x, rotated_y))
        self.vertices = rotated

    def get_hitbox(self) -> List[Vec]:
        """ Returns the actual hitbox vertices (in-world position) """
        real_hitbox = []
        for p in self.vertices:
            real_hitbox.append(p + self.center)
        return real_hitbox

    def project_to_axis(self, axis: Vec) -> Vec:
        # create a "shadow" using dot product
        dots = [point.dot(axis) for point in self.get_hitbox()]
        return Vec(min(dots), max(dots))

    def expand(self, factor: float) -> None:
        new_vertices = []
        for vertex in self.original_vertices:
            new_vertices.append(vertex * factor)
        self.original_vertices = new_vertices

    def is_colliding(self, other: Hitbox) -> bool:
        if isinstance(other, SimpleCircleHitbox):
            return other.is_colliding(self)
        elif isinstance(other, CircleHitbox):
            return other._is_colliding_with_polygon(self)
        elif isinstance(other, RectHitbox):
            return other._is_colliding_with_polygon(self)
        elif isinstance(other, PolygonalHitbox):
            return self._is_colliding_with_polygon(other)
        else:
            raise TypeError(f"Uhhhhh... How did we get here?")

    def _is_colliding_with_polygon(self, other: PolygonalHitbox) -> bool:
        # apparently this method is called the Separating Axis Theorem
        axies = []

        # get all axies from hitboxes, and find their perpendicular axis
        for polygon in (self, other):
            poly = polygon.get_hitbox()
            for i in range(len(poly)):
                point1 = poly[i]
                point2 = poly[(i+1) % len(poly)]
                edge = point2 - point1
                normal = Vec(-edge.y, edge.x).normalize() # rotate 90 degrees and normalize
                axies.append(normal)

        for axis in axies:
            min1, max1 = self.project_to_axis(axis)
            min2, max2 = other.project_to_axis(axis)
            if max1 < min2 or max2 < min1:
                return False # a projection doesn't overlap

        return True # all projections overlap

    def draw(self, target: pygame.Surface, camera_pos: Vec) -> None:
        pygame.draw.polygon(target, (255, 0, 0), [v - camera_pos for v in self.get_hitbox()], 2)

__all__ = [
    "Hitbox",
    "SimpleCircleHitbox",
    "CircleHitbox",
    "RectHitbox",
    "PolygonalHitbox"
]
