#!/usr/bin/env python

from collections import deque
import pylab as pl


class RingArray(deque):
    def __init__(self, max_length):
        super(RingArray, self).__init__(maxlen=max_length)

    def __repr__(self):
        """
        override

        :return:
        """

        l = []

        for i in self:
            l.append(i)

        return str(l)

    def append(self, *args, **kwargs):
        """
        override

        :param args:
        :param kwargs:
        :return:
        """

        if self.maxlen == len(self):
            self.rotate(-1)
            self.pop()
            super(RingArray, self).append(*args, **kwargs)
        else:
            super(RingArray, self).append(*args, **kwargs)


def moving_average(data, num_samples):
    return sum(data) / num_samples


def sort_points(points):
    """
    gets a list of points which are list themselves [x, y]
    it is expected that the list has the length 4

    calculates the top left, bottom left, bottom right and top right corners
    in that order (tl, bl, br, tr) and stores them in a list

    :param points: the unordered list of points with the length 4 (expected)

    :return: the sorted points in the order mentioned above
    """

    sorted_points = []

    x = float('inf')
    x2 = float('inf')
    y = 0
    y2 = 0

    for p in points:
        if p[0] < x:
            x = p[0]
            y = p[1]

            if x < x2:
                temp_x = x
                temp_y = y
                x = x2
                y = y2
                x2 = temp_x
                y2 = temp_y

    if y < y2:
        sorted_points.append([x, y])
        sorted_points.append([x2, y2])
    else:
        sorted_points.append([x2, y2])
        sorted_points.append([x, y])

    x = -1
    x2 = -1
    y = 0
    y2 = 0

    for p in points:
        if p[0] > x:
            x = p[0]
            y = p[1]

            if x > x2:
                temp_x = x
                temp_y = y
                x = x2
                y = y2
                x2 = temp_x
                y2 = temp_y

    if y < y2:
        sorted_points.append([x2, y2])
        sorted_points.append([x, y])
    else:
        sorted_points.append([x, y])
        sorted_points.append([x2, y2])

    return sorted_points


def get_projection_transformed_point(x_values, y_values, monitor_width,
                                     monitor_height, target_point_x,
                                     target_point_y):
    sx1, sy1 = x_values[0], y_values[0]  # tl
    sx2, sy2 = x_values[1], y_values[1]  # bl
    sx3, sy3 = x_values[2], y_values[2]  # br
    sx4, sy4 = x_values[3], y_values[3]  # tr

    source_points_123 = pl.matrix([[sx1, sx2, sx3],
                                   [sy1, sy2, sy3],
                                   [1, 1, 1]])

    source_point_4 = [[sx4], [sy4], [1]]

    scale_to_source = pl.solve(source_points_123, source_point_4)

    l, m, t = [float(x) for x in scale_to_source]

    unit_to_source = pl.matrix([[l * sx1, m * sx2, t * sx3],
                                [l * sy1, m * sy2, t * sy3],
                                [l, m, t]])

    dx1, dy1 = 0, 0
    dx2, dy2 = 0, monitor_height
    dx3, dy3 = monitor_width, monitor_height
    dx4, dy4 = monitor_width, 0

    dest_points_123 = pl.matrix([[dx1, dx2, dx3],
                                 [dy1, dy2, dy3],
                                 [1, 1, 1]])

    dest_point_4 = pl.matrix([[dx4],
                              [dy4],
                              [1]])

    scale_to_dest = pl.solve(dest_points_123, dest_point_4)

    l, m, t = [float(x) for x in scale_to_dest]

    unit_to_dest = pl.matrix([[l * dx1, m * dx2, t * dx3],
                              [l * dy1, m * dy2, t * dy3],
                              [l, m, t]])

    source_to_unit = pl.inv(unit_to_source)

    source_to_dest = unit_to_dest @ source_to_unit

    x, y, z = [float(w) for w in (source_to_dest @ pl.matrix([
        [target_point_x],
        [target_point_y],
        [1]]))]

    x /= z
    y /= z

    y = target_point_y * 2 - y

    return x, y
