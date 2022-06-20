# developed in PyCharm (python 3.9) by Andrii Rybak
import random
from random import randint
import matplotlib.pyplot as plot
import math
import time

GRID_SIZE = 10000
POINTS_NUM = 20000
SQUARE_SIZE = 400

_R = 0
_G = 1
_B = 2
_P = 3


def generate_point(x, y):
    new_point = []
    if random.random() <= 0.99:
        new_point = [randint(x[0], x[1]), randint(y[0], y[1])]
    else:
        new_point = [randint(0, 9999), randint(0, 9999)]
        while x[0] < new_point[0] < x[1] and y[0] < new_point[1] < y[1]:
            new_point = [randint(0, 9999), randint(0, 9999)]

    return new_point


def generate_points():
    cur_type = 0
    cords = []
    types = []

    while len(types) < POINTS_NUM:
        cur_type %= 4

        new_point = []
        if cur_type == _R:
            new_point = generate_point([0, 5500], [0, 5500])
        elif cur_type == _G:
            new_point = generate_point([4500, 9999], [0, 5500])
        elif cur_type == _B:
            new_point = generate_point([0, 5500], [4500, 9999])
        elif cur_type == _P:
            new_point = generate_point([4500, 9999], [4500, 9999])

        if new_point in cords:
            continue
        cords.append(new_point)
        types.append(cur_type)

        cur_type += 1

    return cords, types


def show_graph(classified_points, k, success_rate, time_spent):
    color = []
    x = []
    y = []
    for i in range(len(classified_points)):
        x.append(classified_points[i][0] - 5000)
        y.append(classified_points[i][1] - 5000)
        if classified_points[i][2] == _R:
            color.append("red")
        elif classified_points[i][2] == _G:
            color.append("green")
        elif classified_points[i][2] == _B:
            color.append("blue")
        elif classified_points[i][2] == _P:
            color.append("purple")

    fig = plot.figure()
    ax = fig.add_subplot()
    ax.axis([-5000, 5000, -5000, 5000])
    ax.set_aspect('equal')
    ax.set_xlabel(f"k: {k}; success rate: {success_rate}%; time: {round(time_spent, 2)}s")
    plot.scatter(x, y, c=color, s=50)
    plot.show()


def classify(x, y, classified_points, k):
    distance_and_type = []
    count = [0, 0, 0, 0]

    # calculate distances between point that has to be added and every other point from the nearest squares
    for point in classified_points:
        distance_and_type.append([math.dist([point[0], point[1]], [x, y]), point[2]])
    distance_and_type.sort()

    # count colors of nearest k neighbors
    for i in range(k):
        count[distance_and_type[i][1]] += 1

    return count.index(max(count))


def get_square_cord(x):
    return int(x / SQUARE_SIZE)


def classify_by_squares(x, y, grid, k):
    found_points = []
    square_x = get_square_cord(x)
    square_y = get_square_cord(y)

    squares_distances = []

    # calculate distances between current square and all other
    for i in range(len(grid)):
        for j in range(len(grid)):
            if grid[i][j]:
                squares_distances.append([math.dist([i, j], [square_x, square_y]), i, j])

    squares_distances.sort()

    # choose nearest squares and get points from them
    prev_distance = None
    for cord in squares_distances:
        if prev_distance != cord[0] and len(found_points) >= k:
            break
        found_points += grid[cord[1]][cord[2]]
        prev_distance = cord[0]

    # calculate distances between point that has to be added and every other point from the nearest squares
    distance_and_type = []
    count = [0, 0, 0, 0]
    for point in found_points:
        distance_and_type.append([math.dist([point[0], point[1]], [x, y]), point[2]])
    distance_and_type.sort()

    # count colors of nearest k neighbors
    for i in range(k):
        count[distance_and_type[i][1]] += 1

    return count.index(max(count))


def classify_all(cords, types, classified_points, k, grid):
    wrong_num = 0
    new_color = None

    for i in range(len(cords)):
        if i <= 4000:
            new_color = classify(cords[i][0], cords[i][1], classified_points, k)
        else:
            new_color = classify_by_squares(cords[i][0], cords[i][1], grid, k)

        add_to_grid(grid, [cords[i][0], cords[i][1], new_color])
        classified_points.append([cords[i][0], cords[i][1], new_color])

        if types[i] != new_color:
            wrong_num += 1

    print(f"Success rate: {((POINTS_NUM - wrong_num)/POINTS_NUM)*100}%")

    return ((POINTS_NUM - wrong_num)/POINTS_NUM)*100


def add_to_grid(grid, point):
    grid[int(point[0] / SQUARE_SIZE)][int(point[1] / SQUARE_SIZE)].append(point)


def initialize_start_points(grid):
    classified_points = [[-4500, -4400, _R], [-4100, -3000, _R], [-1800, -2400, _R], [-2500, -3400, _R], [-2000, -1400, _R],
                         [+4500, -4400, _G], [+4100, -3000, _G], [+1800, -2400, _G], [+2500, -3400, _G], [+2000, -1400, _G],
                         [-4500, +4400, _B], [-4100, +3000, _B], [-1800, +2400, _B], [-2500, +3400, _B], [-2000, +1400, _B],
                         [+4500, +4400, _P], [+4100, +3000, _P], [+1800, +2400, _P], [+2500, +3400, _P], [+2000, +1400, _P]]

    for point in classified_points:
        point[0] += 5000
        point[1] += 5000
        add_to_grid(grid, point)

    return classified_points


def test(k_values):

    cords, types = generate_points()
    for k in k_values:
        grid = [[[]] * (int(GRID_SIZE / SQUARE_SIZE)) for _ in range(int(GRID_SIZE / SQUARE_SIZE))]
        classified_points = initialize_start_points(grid)
        print(f"k: {k}")
        start_time = time.time()
        success_rate = classify_all(cords, types, classified_points, k, grid)
        time_spent = time.time() - start_time
        print("--- %s seconds ---" % time_spent)

        show_graph(classified_points, k, success_rate, int(time_spent))


if __name__ == '__main__':
    def main():
        # every number in this list is k
        inputK = [1, 3, 7, 15]

        test(inputK)


    main()
