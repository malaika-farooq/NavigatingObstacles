"""Assigned course input, written in the same form as the assignment PDF header.

Replace these values with the course handed out for the demonstration. Units are
meters; the origin is the lower-left workspace corner, X along the 16-tile side.
Unused obstacle slots stay as (-1, -1), exactly like the PDF example.
"""

TILE_M = 0.305
WORKSPACE_TILES = (16, 10)  # 4.88 m x 3.05 m from the PDF text

MAX_OBSTACLES = 25
num_obstacles = 13

# Assignment PDF example course (page 2). Swap in the assigned course here.
obstacle = [
    (0.61, 2.743), (0.915, 2.743), (1.219, 2.743), (1.829, 1.219),
    (1.829, 1.524), (1.829, 1.829), (1.829, 2.134), (2.743, 0.305),
    (2.743, 0.61), (2.743, 0.915), (2.743, 2.743), (3.048, 2.743),
    (3.353, 2.743),
    (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1),
    (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1),
]

start = (0.305, 1.219)
# Not given by the PDF: the direction the robot faces when placed at start.
# 0 = facing +X (toward the long side), counterclockwise positive.
start_heading_deg = 0.0

goal = (3.658, 1.829)


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
