"""Own four-neighbor BFS planner, conservative footprint, continuous edge checks.

Expanded AABBs overapproximate the circular robot at obstacle corners. A failed
grid search is NOT proof that the physical course has no path. Refine the grid
or footprint model if needed; never silently reduce clearance.
"""
from geometry import segment_hits_box


class CourseMap:
    def __init__(self, course, radius_m, error_m):
        width, height = course["workspace"]
        side = course["obstacle_side"]
        if min(width, height, side, radius_m) <= 0 or error_m < 0:
            raise ValueError("Invalid workspace, obstacle size, or clearance")
        self.margin = radius_m + error_m
        self.width, self.height = width, height
        if 2 * self.margin >= min(width, height):
            raise ValueError("Robot clearance consumes workspace")
        half = side / 2.0 + self.margin
        self.boxes = [(x - half, y - half, x + half, y + half)
                      for x, y in course["obstacles"]]

    def point_clear(self, point):
        x, y = point
        if not (self.margin < x < self.width - self.margin and
                self.margin < y < self.height - self.margin):
            return False
        return not any(x1 <= x <= x2 and y1 <= y <= y2
                       for x1, y1, x2, y2 in self.boxes)

    def segment_clear(self, a, b):
        return (self.point_clear(a) and self.point_clear(b) and
                not any(segment_hits_box(a, b, box) for box in self.boxes))


def simplify(path):
    if len(path) <= 2:
        return path[:]
    result = [path[0]]
    for i in range(1, len(path) - 1):
        a, b, c = result[-1], path[i], path[i + 1]
        cross = (b[0]-a[0])*(c[1]-b[1]) - (b[1]-a[1])*(c[0]-b[0])
        dot = (b[0]-a[0])*(c[0]-b[0]) + (b[1]-a[1])*(c[1]-b[1])
        if abs(cross) > 1e-9 or dot <= 0:
            result.append(b)
    result.append(path[-1])
    return result


def plan(course, radius_m, error_m, spacing_m, max_nodes=10000):
    if spacing_m <= 0:
        raise ValueError("Grid spacing must be positive")
    world = CourseMap(course, radius_m, error_m)
    start, goal = tuple(course["start"]), tuple(course["goal"])
    if not world.point_clear(start) or not world.point_clear(goal):
        raise ValueError("Start/goal violates the configured clearance model")
    if world.segment_clear(start, goal):
        return [start] if start == goal else [start, goal]
    nx = int(world.width / spacing_m)
    ny = int(world.height / spacing_m)
    if nx * ny > max_nodes:
        raise ValueError("Grid exceeds memory budget; increase spacing or node limit")
    nodes = {}
    parents = {}
    queue = []
    goals = set()
    # Grid anchored to the course origin; start/goal are exact virtual endpoints.
    for iy in range(1, ny + 1):
        for ix in range(1, nx + 1):
            point = (ix * spacing_m, iy * spacing_m)
            if not world.point_clear(point):
                continue
            index = (ix, iy)
            nodes[index] = point
            if world.segment_clear(start, point):
                parents[index] = None
                queue.append(index)
            if world.segment_clear(point, goal):
                goals.add(index)
    head = 0
    end = None
    while head < len(queue):
        index = queue[head]
        head += 1
        if index in goals:
            end = index
            break
        ix, iy = index
        for neighbor in ((ix-1, iy), (ix+1, iy), (ix, iy-1), (ix, iy+1)):
            if neighbor in nodes and neighbor not in parents:
                if world.segment_clear(nodes[index], nodes[neighbor]):
                    parents[neighbor] = index
                    queue.append(neighbor)
    if end is None:
        raise ValueError("No route in this grid/clearance model; refine or inspect course")
    chain = []
    while end is not None:
        chain.append(nodes[end])
        end = parents[end]
    chain.reverse()
    path = simplify([start] + chain + [goal])
    if not all(world.segment_clear(a, b) for a, b in zip(path, path[1:])):
        raise ValueError("Internal error: generated path failed clearance validation")
    return path


def demo_course():
    """Synthetic test fixture; never the supplied assignment course."""
    return {"workspace": (3.0, 2.0), "start": (0.4, 1.0), "goal": (2.6, 1.0),
            "obstacles": [(1.5, 1.0)], "obstacle_side": 0.305}
