#!/usr/bin/env python

from collections import deque
import numpy as np


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
