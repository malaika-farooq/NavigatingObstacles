"""Course input, written in the same form as the assignment PDF header.

"""

TILE_M = 0.305  
WORKSPACE_TILES = (16, 10)  # 4.88 m x 3.05 m

MAX_OBSTACLES = 25
num_obstacles = 18  # demo instruction by prof

obstacle = [
    (0.915, 0.305), (0.915, 0.61), (0.915, 0.915), (0.915, 1.22),
    (0.915, 1.525), (0.915, 1.833), (1.83, 1.22), (1.83, 1.525),
    (1.83, 1.83), (1.83, 2.135), (1.83, 2.44), (1.83, 2.745),
    (2.745, 1.525), (2.745, 1.83), (3.355, 0.915), (3.355, 1.22),
    (3.66, 0.915), (3.66, 1.22),
    (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1),
    (-1, -1),
]

start = (0.305, 0.61)


goal = (3.66, 1.83)


def workspace_m():
    width_m = WORKSPACE_TILES[0] * TILE_M
    height_m = WORKSPACE_TILES[1] * TILE_M
    return (width_m, height_m)


def obstacle_centers_m():
    """Return the first num_obstacles entries, rejecting padding or bad counts."""
    if not 0 <= num_obstacles <= MAX_OBSTACLES:
        raise ValueError("num_obstacles must be between 0 and MAX_OBSTACLES")
    if len(obstacle) < num_obstacles:
        raise ValueError("obstacle list is shorter than num_obstacles")
    centers = []
    for center_x_m, center_y_m in obstacle[:num_obstacles]:
        if center_x_m < 0 or center_y_m < 0:
            raise ValueError("Padding (-1, -1) found inside num_obstacles")
        centers.append((float(center_x_m), float(center_y_m)))
    return centers
