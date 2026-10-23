"""Plan with the Manhattan-distance navigation function (wavefront) from lecture.

Goal cell = 0, neighbors +1; the robot descends the potential to the goal.

The circular robot envelope is approximated conservatively at obstacle corners.
A failed grid search is not proof that the physical course has no route.
"""
from geometry import INFINITY, distance, segment_hits_box


class CourseMap:
    def __init__(self, course, radius_m, error_m):
        workspace_width_m, workspace_height_m = course["workspace"]
        obstacle_side_m = course["obstacle_side"]
        if min(workspace_width_m, workspace_height_m, obstacle_side_m, radius_m) <= 0 or error_m < 0:
            raise ValueError("Invalid workspace, obstacle size, or clearance")
        self.margin = radius_m + error_m
        self.width = workspace_width_m
        self.height = workspace_height_m
        if 2 * self.margin >= min(self.width, self.height):
            raise ValueError("Robot clearance consumes workspace")
        expanded_half_side_m = obstacle_side_m / 2.0 + self.margin
        self.boxes = []
        for center_x_m, center_y_m in course["obstacles"]:
            obstacle_box = (center_x_m - expanded_half_side_m, center_y_m - expanded_half_side_m,
                            center_x_m + expanded_half_side_m, center_y_m + expanded_half_side_m)
            self.boxes.append(obstacle_box)

    def point_clear(self, point):
        point_x_m = point[0]
        point_y_m = point[1]
        inside_x = self.margin < point_x_m < self.width - self.margin
        inside_y = self.margin < point_y_m < self.height - self.margin
        if not inside_x or not inside_y:
            return False
        for minimum_x, minimum_y, maximum_x, maximum_y in self.boxes:
            inside_obstacle_x = minimum_x <= point_x_m <= maximum_x
            inside_obstacle_y = minimum_y <= point_y_m <= maximum_y
            if inside_obstacle_x and inside_obstacle_y:
                return False
        return True

    def segment_clear(self, start, end):
        if not self.point_clear(start) or not self.point_clear(end):
            return False
        for obstacle_box in self.boxes:
            if segment_hits_box(start, end, obstacle_box):
                return False
        return True


def _same_direction(start, middle, end):
    first_x = middle[0] - start[0]
    first_y = middle[1] - start[1]
    second_x = end[0] - middle[0]
    second_y = end[1] - middle[1]
    cross_product = first_x * second_y - first_y * second_x
    dot_product = first_x * second_x + first_y * second_y
    collinear = abs(cross_product) <= 1e-9
    continues_forward = dot_product > 0
    return collinear and continues_forward


def simplify(path):
    if len(path) <= 2:
        return path[:]
    result = [path[0]]
    for point_index in range(1, len(path) - 1):
        previous_point = result[-1]
        current_point = path[point_index]
        next_point = path[point_index + 1]
        if not _same_direction(previous_point, current_point, next_point):
            result.append(current_point)
    result.append(path[-1])
    return result


def _build_grid(world, spacing_m, max_nodes):
    column_count = int(world.width / spacing_m)
    row_count = int(world.height / spacing_m)
    grid_size = column_count * row_count
    if grid_size > max_nodes:
        raise ValueError("Grid exceeds memory budget; increase spacing or node limit")
    nodes = {}
    for row in range(1, row_count + 1):
        for column in range(1, column_count + 1):
            position_m = (column * spacing_m, row * spacing_m)
            if world.point_clear(position_m):
                nodes[(column, row)] = position_m
    return nodes


# Four Manhattan neighbors, listed so index i and (i + 2) % 4 are opposites.
STEPS = ((1, 0), (0, 1), (-1, 0), (0, -1))
UNREACHED = -1


def _endpoint_cells(world, nodes, endpoint):
    """All grid cells with a collision-free connector to an exact endpoint."""
    connections = []
    for cell, position_m in nodes.items():
        if world.segment_clear(endpoint, position_m):
            connections.append(cell)
    if not connections:
        raise ValueError("Start or goal cannot reach a free grid cell")
    return connections


def wavefront(world, nodes, goal_cells):
    """Label goal-connected cells 0, then spread +1 through clear grid edges.

    One seed gives the usual Manhattan wavefront. Multiple seeds represent
    independently checked straight-line connections to the exact goal.
    Cells absent from the result are blocked or unreachable.
    """
    potential = {}
    frontier = []
    for cell in goal_cells:
        if cell not in potential:
            potential[cell] = 0
            frontier.append(cell)
    frontier_position = 0
    while frontier_position < len(frontier):
        cell = frontier[frontier_position]
        frontier_position += 1
        for step_x, step_y in STEPS:
            neighbor = (cell[0] + step_x, cell[1] + step_y)
            if neighbor not in nodes or neighbor in potential:
                continue
            if not world.segment_clear(nodes[cell], nodes[neighbor]):
                continue
            potential[neighbor] = potential[cell] + 1
            frontier.append(neighbor)
    return potential


def _start_cell(nodes, potential, connections, start):
    """Prefer the nearest start connector that can reach a goal connector."""
    best_cell = None
    best_distance_m = INFINITY
    for cell in connections:
        if cell not in potential:
            continue
        connector_distance_m = distance(start, nodes[cell])
        if connector_distance_m < best_distance_m:
            best_cell = cell
            best_distance_m = connector_distance_m
    if best_cell is None:
        raise ValueError("No route in this grid/clearance model; refine or inspect course")
    return best_cell


def descend(world, nodes, potential, start_index):
    """Follow the gradient to the goal; keep the current direction on ties (fewer turns)."""
    if start_index not in potential:
        raise ValueError("No route in this grid/clearance model; refine or inspect course")
    cells = [start_index]
    cell = start_index
    direction = None
    while potential[cell] > 0:
        target_value = potential[cell] - 1
        choices = []
        for step_index in range(4):
            step_x, step_y = STEPS[step_index]
            neighbor = (cell[0] + step_x, cell[1] + step_y)
            if potential.get(neighbor, UNREACHED) != target_value:
                continue
            if not world.segment_clear(nodes[cell], nodes[neighbor]):
                continue
            choices.append(step_index)
        if not choices:
            raise ValueError("Navigation function has no downhill neighbor")
        direction = direction if direction in choices else choices[0]
        step_x, step_y = STEPS[direction]
        cell = (cell[0] + step_x, cell[1] + step_y)
        cells.append(cell)
    return cells


def _validate_path(world, path):
    for point_index in range(len(path) - 1):
        segment_start = path[point_index]
        segment_end = path[point_index + 1]
        if not world.segment_clear(segment_start, segment_end):
            raise ValueError("Generated path failed clearance validation")


def plan(course, radius_m, error_m, spacing_m, max_nodes=10000):
    """Waypoints from start to goal using the Manhattan-distance navigation function.

    1. Configuration space: grow each square and the walls by radius_m + error_m.
    2. Regular grid: cells every spacing_m; cells inside grown obstacles are removed.
    3. Wavefront: seed all goal-connected cells and spread +1 to 4-neighbors.
    4. Descend from a reachable start connector, keeping direction on ties.
    5. Merge straight runs into single drive segments.
    """
    if spacing_m <= 0:
        raise ValueError("Grid spacing must be positive")
    world = CourseMap(course, radius_m, error_m)
    start = tuple(course["start"])
    goal = tuple(course["goal"])
    if not world.point_clear(start) or not world.point_clear(goal):
        raise ValueError("Start/goal violates the configured clearance model")
    if world.segment_clear(start, goal):
        return [start] if start == goal else [start, goal]
    nodes = _build_grid(world, spacing_m, max_nodes)
    start_connections = _endpoint_cells(world, nodes, start)
    goal_connections = _endpoint_cells(world, nodes, goal)
    potential = wavefront(world, nodes, goal_connections)
    start_index = _start_cell(nodes, potential, start_connections, start)
    cells = descend(world, nodes, potential, start_index)
    grid_points = [nodes[cell] for cell in cells]
    path = _without_repeats([start] + grid_points + [goal])
    path = simplify(path)
    _validate_path(world, path)
    return path


def _without_repeats(points):
    """Remove only consecutive identical points; nearby corners can be essential."""
    result = [points[0]]
    for point in points[1:]:
        if point != result[-1]:
            result.append(point)
    return result


def demo_course():
    """Synthetic test course, not the assigned configuration."""
    return {"workspace": (3.0, 2.0), "start": (0.4, 1.0), "goal": (2.6, 1.0),
            "obstacles": [(1.5, 1.0)], "obstacle_side": 0.305, "goal_radius": 0.305}
