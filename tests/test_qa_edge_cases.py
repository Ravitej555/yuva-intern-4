"""
Quality Assurance Unit Tests: Boundary Conditions, Mathematical Singularities, and Edge Cases.
Week 4 Deliverable - Comprehensive Testing & Quality Assurance Suite.
"""
import sys
import math
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game_module.physics.vector2 import Vector2
from game_module.physics.aabb import AABB
from game_module.physics.rigidbody import Rigidbody, BodyType
from game_module.physics.world import PhysicsWorld
from game_module.ai.pathfinding import AStarPathfinder
from game_module.input.handler import InputHandler, Action


class TestQAEdgeCases(unittest.TestCase):
    """Rigorous boundary and mathematical singularity verification."""

    # -------------------------------------------------------------
    # Vector2 Singularities & Invariants
    # -------------------------------------------------------------
    def test_vector2_zero_magnitude_normalization(self):
        """TC-VEC-01: Verify normalization of (0,0) safely returns (0,0) without ZeroDivisionError."""
        v = Vector2(0.0, 0.0)
        norm = v.normalized()
        self.assertEqual(norm.x, 0.0)
        self.assertEqual(norm.y, 0.0)
        self.assertEqual(norm, Vector2.zero())

    def test_vector2_extreme_division(self):
        """TC-VEC-02: Verify division by zero and near-zero floats behaves gracefully."""
        v = Vector2(100.0, -250.0)
        div_zero = v / 0.0
        self.assertEqual(div_zero, Vector2.zero())
        
        # In-place division
        v /= 0.0
        self.assertEqual(v, Vector2.zero())

    def test_vector2_dot_product_orthogonality(self):
        """TC-VEC-03: Verify dot product commutativity and orthogonality invariant."""
        v1 = Vector2(1.0, 0.0)
        v2 = Vector2(0.0, 1.0)
        self.assertEqual(v1.dot(v2), 0.0)
        self.assertEqual(v2.dot(v1), 0.0)
        
        # Parallel and anti-parallel
        self.assertAlmostEqual(v1.dot(v1), 1.0)
        self.assertAlmostEqual(v1.dot(Vector2(-1.0, 0.0)), -1.0)

    def test_vector2_lerp_boundaries(self):
        """TC-VEC-04: Verify linear interpolation at boundaries t=0, t=1, and clamped ranges."""
        a = Vector2(0.0, 0.0)
        b = Vector2(10.0, 20.0)
        self.assertEqual(a.lerp(b, 0.0), a)
        self.assertEqual(a.lerp(b, 1.0), b)
        mid = a.lerp(b, 0.5)
        self.assertAlmostEqual(mid.x, 5.0)
        self.assertAlmostEqual(mid.y, 10.0)

    # -------------------------------------------------------------
    # AABB Boundary & Geometric Degeneracy
    # -------------------------------------------------------------
    def test_aabb_touching_borders(self):
        """TC-AABB-01: Verify exact touching AABB borders (coincident edges) are handled correctly."""
        # Box 1 from (0,0) to (2,2) -> center (1,1), half_size (1,1)
        # Box 2 from (2,0) to (4,2) -> center (3,1), half_size (1,1)
        b1 = AABB.from_min_max(Vector2(0.0, 0.0), Vector2(2.0, 2.0))
        b2 = AABB.from_min_max(Vector2(2.0, 0.0), Vector2(4.0, 2.0))
        
        # Touching at x = 2.0. In standard continuous collision, touching has zero penetration depth
        mtv = b1.intersection_depth(b2)
        # MTV depth at touching edge is zero or None
        if mtv is not None:
            self.assertAlmostEqual(mtv.magnitude(), 0.0, delta=1e-5)

    def test_aabb_concentric_boxes(self):
        """TC-AABB-02: Concentric boxes where one is completely enclosed within another."""
        outer = AABB.from_min_max(Vector2(0.0, 0.0), Vector2(10.0, 10.0))
        inner = AABB.from_min_max(Vector2(4.0, 4.0), Vector2(6.0, 6.0))
        self.assertTrue(outer.intersects(inner))
        self.assertTrue(inner.intersects(outer))
        self.assertTrue(outer.contains_point(Vector2(5.0, 5.0)))
        
        # Points on corners
        self.assertTrue(outer.contains_point(Vector2(0.0, 0.0)))
        self.assertTrue(outer.contains_point(Vector2(10.0, 10.0)))
        self.assertFalse(outer.contains_point(Vector2(10.01, 10.0)))

    # -------------------------------------------------------------
    # Rigidbody & PhysicsWorld Dynamics Singularities
    # -------------------------------------------------------------
    def test_rigidbody_zero_and_infinite_mass(self):
        """TC-RB-01: Static bodies with infinite mass (inv_mass == 0) must never move under forces."""
        static_body = Rigidbody(
            name="anchor",
            body_type=BodyType.STATIC,
            position=Vector2(5.0, 5.0),
            mass=0.0  # static bodies have mass 0.0 -> inv_mass 0.0
        )
        self.assertEqual(static_body.inv_mass, 0.0)
        
        # Applying impulse or force must NOT alter velocity or position
        static_body.add_impulse(Vector2(500.0, -500.0))
        static_body.add_force(Vector2(1000.0, 2000.0))
        static_body.integrate(0.016, Vector2(0, 20.0))
        
        self.assertEqual(static_body.velocity, Vector2.zero())
        self.assertEqual(static_body.position, Vector2(5.0, 5.0))

    def test_physics_world_zero_and_negative_dt(self):
        """TC-PWR-01: Passing dt <= 0 to physics world step must safely no-op without corrupting state."""
        world = PhysicsWorld(gravity=Vector2(0, 20.0))
        body = Rigidbody(body_type=BodyType.DYNAMIC, position=Vector2(0, 0), velocity=Vector2(5, 5))
        world.add_body(body)
        
        initial_pos = body.position.copy()
        initial_vel = body.velocity.copy()
        
        world.step(0.0)
        world.step(-0.016)
        
        self.assertEqual(body.position, initial_pos)
        self.assertEqual(body.velocity, initial_vel)

    def test_raycast_parallel_and_glancing_miss(self):
        """TC-PWR-02: Raycast parallel to box edges must detect hits only if collinearly intersecting."""
        world = PhysicsWorld()
        box = Rigidbody(body_type=BodyType.STATIC, position=Vector2(10.0, 10.0), size=Vector2(2.0, 2.0))
        world.add_body(box)
        
        # Ray passing right above the box (y = 8.95 while box min_y is 9.0)
        miss_hits = world.raycast_aabb(Vector2(0.0, 8.9), Vector2(1.0, 0.0), max_dist=20.0)
        self.assertEqual(len(miss_hits), 0)
        
        # Ray directly hitting the center
        hit_hits = world.raycast_aabb(Vector2(0.0, 10.0), Vector2(1.0, 0.0), max_dist=20.0)
        self.assertEqual(len(hit_hits), 1)
        self.assertAlmostEqual(hit_hits[0][1], 9.0)  # Box min_x is 10.0 - 1.0 = 9.0

    # -------------------------------------------------------------
    # A* Pathfinding Degeneracy
    # -------------------------------------------------------------
    def test_astar_start_equals_goal(self):
        """TC-AST-01: When start and goal are in the exact same cell, return single trivial path point."""
        grid = [[0, 0], [0, 0]]
        pf = AStarPathfinder(grid, cell_size=1.0)
        path = pf.find_path(Vector2(0.5, 0.5), Vector2(0.5, 0.5))
        self.assertEqual(len(path), 1)
        self.assertEqual(path[0], Vector2(0.5, 0.5))

    def test_astar_start_or_goal_in_solid_wall(self):
        """TC-AST-02: If start or goal lies inside an impassable obstacle, return empty path gracefully."""
        grid = [
            [1, 0],
            [0, 0]
        ]
        pf = AStarPathfinder(grid, cell_size=1.0)
        # Start in solid cell (0, 0)
        path1 = pf.find_path(Vector2(0.5, 0.5), Vector2(1.5, 1.5))
        self.assertEqual(path1, [])
        
        # Goal in solid cell (0, 0)
        path2 = pf.find_path(Vector2(1.5, 1.5), Vector2(0.5, 0.5))
        self.assertEqual(path2, [])

    # -------------------------------------------------------------
    # Input Buffer & Transient State Invariants
    # -------------------------------------------------------------
    def test_input_simultaneous_opposing_axes(self):
        """TC-INP-01: Holding opposing directional actions (LEFT + RIGHT) must result in 0.0 net axis."""
        ih = InputHandler()
        ih.feed("a", True)
        ih.feed("d", True)
        ih.update(0.016)
        
        axis = ih.get_axis(Action.MOVE_LEFT, Action.MOVE_RIGHT)
        self.assertEqual(axis, 0.0, "Opposing inputs must cancel out cleanly.")


if __name__ == "__main__":
    unittest.main()
