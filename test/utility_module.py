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
