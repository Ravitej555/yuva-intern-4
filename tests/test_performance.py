"""
Performance Benchmark Tests for Game Module.
Measures execution time and resource usage to ensure the module
meets real-time performance requirements (60 FPS = 16.67ms per frame).
"""
import sys
from pathlib import Path
import math
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game_module.physics.vector2 import Vector2
from game_module.physics.rigidbody import Rigidbody, BodyType
from game_module.physics.world import PhysicsWorld
from game_module.ai.pathfinding import AStarPathfinder
from game_module.ai.state_machine import StateMachine, State
from game_module.input.handler import InputHandler, Action
from game_module.entities.player import Player
from game_module.entities.enemy import Enemy


class TestPerformanceBenchmarks(unittest.TestCase):
    """TC-PF-01 through TC-PF-08: Performance benchmarks for real-time requirements."""

    FRAME_BUDGET_MS = 16.67  # 60 FPS target

    def test_physics_step_10_bodies(self):
        """TC-PF-01: Physics step with 10 bodies should complete within frame budget."""
        world = PhysicsWorld(gravity=Vector2(0, 10), sub_steps=4)
        ground = Rigidbody(body_type=BodyType.STATIC, position=Vector2(50, 100),
                           size=Vector2(200, 10))
        world.add_body(ground)
        for i in range(10):
            b = Rigidbody(position=Vector2(i * 5, 0), size=Vector2(1, 1), mass=1.0)
            world.add_body(b)

        start = time.perf_counter()
        for _ in range(60):
            world.step(1/60)
        elapsed_ms = (time.perf_counter() - start) * 1000 / 60

        print(f"\n  [TC-PF-01] Avg frame time (10 bodies): {elapsed_ms:.3f}ms")
        self.assertLess(elapsed_ms, self.FRAME_BUDGET_MS,
                        f"Frame time {elapsed_ms:.2f}ms exceeds budget {self.FRAME_BUDGET_MS}ms")

    def test_physics_step_50_bodies(self):
        """TC-PF-02: Physics step with 50 bodies should complete within frame budget."""
        world = PhysicsWorld(gravity=Vector2(0, 10), sub_steps=4)
        ground = Rigidbody(body_type=BodyType.STATIC, position=Vector2(50, 100),
                           size=Vector2(200, 10))
        world.add_body(ground)
        for i in range(50):
            b = Rigidbody(position=Vector2(i * 2, i % 10), size=Vector2(1, 1), mass=1.0)
            world.add_body(b)

        start = time.perf_counter()
        for _ in range(60):
            world.step(1/60)
        elapsed_ms = (time.perf_counter() - start) * 1000 / 60

        print(f"\n  [TC-PF-02] Avg frame time (50 bodies): {elapsed_ms:.3f}ms")
        self.assertLess(elapsed_ms, self.FRAME_BUDGET_MS,
                        f"Frame time {elapsed_ms:.2f}ms exceeds budget {self.FRAME_BUDGET_MS}ms")

    def test_physics_step_100_bodies_stress(self):
        """TC-PF-03: Stress test - 100 bodies should stay under 2x frame budget."""
        world = PhysicsWorld(gravity=Vector2(0, 10), sub_steps=4)
        ground = Rigidbody(body_type=BodyType.STATIC, position=Vector2(50, 100),
                           size=Vector2(200, 10))
        world.add_body(ground)
        for i in range(100):
            b = Rigidbody(position=Vector2(i % 20 * 3, i // 20 * 3),
                          size=Vector2(1, 1), mass=1.0)
            world.add_body(b)

        start = time.perf_counter()
        for _ in range(60):
            world.step(1/60)
        elapsed_ms = (time.perf_counter() - start) * 1000 / 60

        print(f"\n  [TC-PF-03] Avg frame time (100 bodies): {elapsed_ms:.3f}ms")
        self.assertLess(elapsed_ms, self.FRAME_BUDGET_MS * 2,
                        f"Stress frame time {elapsed_ms:.2f}ms exceeds 2x budget")

    def test_pathfinding_small_grid(self):
        """TC-PF-04: A* on 20x20 grid should complete within 5ms."""
        grid = [[0]*20 for _ in range(20)]
        grid[5][5:15] = [1]*10  # Add wall
        pf = AStarPathfinder(grid, cell_size=1.0)

        start = time.perf_counter()
        for _ in range(100):
            pf.find_path(Vector2(0.5, 0.5), Vector2(19.5, 19.5))
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100

        print(f"\n  [TC-PF-04] Avg pathfinding time (20x20): {elapsed_ms:.3f}ms")
        self.assertLess(elapsed_ms, 5.0,
                        f"Pathfinding {elapsed_ms:.2f}ms exceeds 5ms budget")

    def test_pathfinding_large_grid(self):
        """TC-PF-05: A* on 50x50 grid should complete within 50ms."""
        grid = [[0]*50 for _ in range(50)]
        for i in range(10, 40):
            grid[25][i] = 1  # Add wall
        pf = AStarPathfinder(grid, cell_size=1.0)

        start = time.perf_counter()
        for _ in range(10):
            pf.find_path(Vector2(0.5, 0.5), Vector2(49.5, 49.5))
        elapsed_ms = (time.perf_counter() - start) * 1000 / 10

        print(f"\n  [TC-PF-05] Avg pathfinding time (50x50): {elapsed_ms:.3f}ms")
        self.assertLess(elapsed_ms, 50.0,
                        f"Pathfinding {elapsed_ms:.2f}ms exceeds 50ms budget")

    def test_input_handler_throughput(self):
        """TC-PF-06: Input handler should process 1000 frames/sec of input."""
        ih = InputHandler()
        keys = ["a", "d", "w", "s", "space", "j"]

        start = time.perf_counter()
        for i in range(1000):
            for k in keys:
                ih.feed(k, i % 2 == 0)
            ih.update(0.016)
            ih.is_action_pressed(Action.JUMP)
            ih.get_axis(Action.MOVE_LEFT, Action.MOVE_RIGHT)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n  [TC-PF-06] Input handler 1000 frames: {elapsed_ms:.1f}ms total")
        self.assertLess(elapsed_ms, 500.0,
                        f"Input processing {elapsed_ms:.1f}ms exceeds 500ms for 1000 frames")

    def test_vector2_operations_throughput(self):
        """TC-PF-07: 100K vector operations should complete within 500ms."""
        a = Vector2(3.0, 4.0)
        b = Vector2(1.0, 2.0)

        start = time.perf_counter()
        for _ in range(100_000):
            c = a + b
            d = a - b
            _ = a.dot(b)
            _ = a.magnitude()
            _ = a.normalized()
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n  [TC-PF-07] 100K vector ops: {elapsed_ms:.1f}ms")
        self.assertLess(elapsed_ms, 500.0,
                        f"Vector ops {elapsed_ms:.1f}ms exceeds 500ms budget")

    def test_full_game_loop_performance(self):
        """TC-PF-08: Full game loop (physics + AI + input) should meet 60 FPS."""
        world = PhysicsWorld(gravity=Vector2(0, 20), sub_steps=4)
        ground = Rigidbody(body_type=BodyType.STATIC, position=Vector2(10, 10),
                           size=Vector2(20, 2))
        world.add_body(ground)

        player_body = Rigidbody(position=Vector2(3, 5), size=Vector2(1, 1.4), mass=1.0)
        world.add_body(player_body)
        ih = InputHandler()
        player = Player(body=player_body, input=ih)

        enemy_body = Rigidbody(position=Vector2(15, 5), size=Vector2(1, 1.4), mass=1.0)
        world.add_body(enemy_body)
        enemy = Enemy(body=enemy_body, player_pos=player_body.position.copy())

        dt = 1 / 60
        start = time.perf_counter()
        for i in range(300):
            ih.feed("d", i % 60 < 30)
            ih.update(dt)
            player.update(dt)
            enemy.update(dt, player.body.position)
            world.step(dt)
        total_ms = (time.perf_counter() - start) * 1000
        avg_ms = total_ms / 300

        print(f"\n  [TC-PF-08] Full game loop avg: {avg_ms:.3f}ms/frame ({1000/avg_ms:.0f} FPS)")
        self.assertLess(avg_ms, self.FRAME_BUDGET_MS,
                        f"Full loop {avg_ms:.2f}ms exceeds {self.FRAME_BUDGET_MS}ms budget")


class TestSimulationDeterminism(unittest.TestCase):
    """TC-PF-09 through TC-PF-10: Determinism and stability tests."""

    def test_deterministic_simulation(self):
        """TC-PF-09: Same inputs should produce identical outputs across runs."""
        results = []
        for _ in range(3):
            world = PhysicsWorld(gravity=Vector2(0, 10), sub_steps=4)
            body = Rigidbody(position=Vector2(5, 0), velocity=Vector2(2, 0), mass=1.0)
            ground = Rigidbody(body_type=BodyType.STATIC, position=Vector2(5, 10),
                               size=Vector2(20, 2))
            world.add_body(body)
            world.add_body(ground)
            for _ in range(120):
                world.step(1/60)
            results.append((body.position.x, body.position.y))

        for r in results[1:]:
            self.assertAlmostEqual(results[0][0], r[0], places=10)
            self.assertAlmostEqual(results[0][1], r[1], places=10)

    def test_long_simulation_stability(self):
        """TC-PF-10: 10-second simulation should not produce NaN or Inf values."""
        world = PhysicsWorld(gravity=Vector2(0, 10), sub_steps=4)
        bodies = []
        ground = Rigidbody(body_type=BodyType.STATIC, position=Vector2(10, 20),
                           size=Vector2(30, 2))
        world.add_body(ground)
        for i in range(20):
            b = Rigidbody(position=Vector2(i * 1.5, 0), size=Vector2(1, 1), mass=1.0)
            world.add_body(b)
            bodies.append(b)

        for _ in range(600):  # 10 seconds at 60 FPS
            world.step(1/60)

        for b in bodies:
            self.assertTrue(math.isfinite(b.position.x), f"Body {b.name} has NaN/Inf x")
            self.assertTrue(math.isfinite(b.position.y), f"Body {b.name} has NaN/Inf y")
            self.assertTrue(math.isfinite(b.velocity.x), f"Body {b.name} has NaN/Inf vx")
            self.assertTrue(math.isfinite(b.velocity.y), f"Body {b.name} has NaN/Inf vy")


if __name__ == "__main__":
    unittest.main()
