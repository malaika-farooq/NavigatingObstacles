"""Plan around known cardboard squares using our own four-neighbor BFS.

The circular robot envelope is approximated conservatively at obstacle corners.
A failed grid search is not proof that the physical course has no route.
"""
from geometry import segment_hits_box


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


def _connect_endpoints(world, nodes, start, goal):
    parents = {}
    queue = []
    goal_connections = set()
    for index, position_m in nodes.items():
        if world.segment_clear(start, position_m):
            parents[index] = None
            queue.append(index)
        if world.segment_clear(position_m, goal):
            goal_connections.add(index)
    return parents, queue, goal_connections


def _neighbors(index):
    column, row = index
    return ((column - 1, row), (column + 1, row), (column, row - 1), (column, row + 1))


def _search_grid(world, nodes, parents, queue, goal_connections):
    queue_position = 0
    while queue_position < len(queue):
        current_index = queue[queue_position]
        queue_position += 1
        if current_index in goal_connections:
            return current_index
        for neighbor_index in _neighbors(current_index):
            unvisited_node = neighbor_index in nodes and neighbor_index not in parents
            if not unvisited_node:
                continue
            current_position = nodes[current_index]
            neighbor_position = nodes[neighbor_index]
            if world.segment_clear(current_position, neighbor_position):
                parents[neighbor_index] = current_index
                queue.append(neighbor_index)
    raise ValueError("No route in this grid/clearance model; refine or inspect course")


def _reconstruct_path(nodes, parents, final_index, start, goal):
    reversed_points = []
    current_index = final_index
    while current_index is not None:
        reversed_points.append(nodes[current_index])
        current_index = parents[current_index]
    reversed_points.reverse()
    return simplify([start] + reversed_points + [goal])


def _validate_path(world, path):
    for point_index in range(len(path) - 1):
        segment_start = path[point_index]
        segment_end = path[point_index + 1]
        if not world.segment_clear(segment_start, segment_end):
            raise ValueError("Generated path failed clearance validation")


def plan(course, radius_m, error_m, spacing_m, max_nodes=10000):
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
    parents, queue, goal_connections = _connect_endpoints(world, nodes, start, goal)
    final_index = _search_grid(world, nodes, parents, queue, goal_connections)
    path = _reconstruct_path(nodes, parents, final_index, start, goal)
    _validate_path(world, path)
    return path


def demo_course():
    """Synthetic test course, not the assigned configuration."""
    return {"workspace": (3.0, 2.0), "start": (0.4, 1.0), "goal": (2.6, 1.0),
            "obstacles": [(1.5, 1.0)], "obstacle_side": 0.305, "goal_radius": 0.305}
