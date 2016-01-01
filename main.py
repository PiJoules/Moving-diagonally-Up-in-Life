#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import math
import os


class Point(object):
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, o):
        return isinstance(o, Point) and self.x == o.x and self.y == o.y

    def __hash__(self):
        return hash((self.x, self.y, ))

    @property
    def coords(self):
        return self.x, self.y

    def __str__(self):
        return "({},{})".format(self.x, self.y)


class Grid(object):
    def __init__(self, grid):
        self.grid = grid
        assert all(map(lambda x: len(x) == self.width, grid))
        assert len(grid) == self.height

        self.cols = map(lambda y: "".join(map(lambda x: x[y], grid)),
                        xrange(self.width))
        self.rows = grid
        self.visited = set()
        points = []
        for y in range(len(grid))[::-1]:  # Start bottom up
            for x in xrange(len(grid[0])):  # Left right
                if grid[y][x] == "X":
                    points.append(Point(x, y))
        if len(points) < 1:
            raise RuntimeError("Unable to find starting coord from grid.")
        self._start = points[0]
        self._end = points[-1]
        self.points = points
        self._paths = None
        self._is_possible = None

    @classmethod
    def from_stdin(cls):
        return cls.from_stream(sys.stdin)

    @classmethod
    def from_stream(cls, stream):
        width, height = stream.readline().split(",")
        grid = []
        for line in stream:
            line = line.strip()
            grid.append(line)
        return cls(grid)

    @classmethod
    def from_file(cls, filename):
        assert os.path.isfile(filename)
        with open(filename, "r") as f:
            return cls.from_stream(f)

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def paths_count(self):
        if self._paths is None:
            if len(self.points) <= 0:
                self._paths = 0
            elif len(self.points) == 1:
                self._paths = 1
            elif self.is_possible:
                paths = 1
                for i, p in enumerate(self.points[1:]):
                    last_p = self.points[i]  # i still starts at 0
                    sub = Subgrid.from_points(self.grid, last_p, p)
                    paths *= len(sub.paths)
                self._paths = paths
            else:
                self._paths = None
        return self._paths

    @property
    def width(self):
        return len(self.grid[0])

    @property
    def height(self):
        return len(self.grid)

    def _nothing_before(self, x, y):
        """
        Make sure no other X exists in the row/col
        before the given coords.
        """
        for p in self.points:
            if p not in self.visited:
                if p.x < x or p.y > y:
                    return False
        return True

    def _mutually_exclusive_row_col(self, x, y):
        """
        All other Xs exist either on the same row or
        col, but never both.
        """
        cols = self.cols[:x] + self.cols[x + 1:]
        rows = self.rows[:y] + self.rows[y + 1:]
        return not ("X" in cols and "X" in rows)

    def _get_nearest(self, x, y):
        """
        Get the nearest X from the current one through
        only valid moves.
        """
        def dist(x1, y1, x2, y2):
            return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        valid_points = filter(
            lambda p: p.x >= x and p.y <= y and not (p.x == x and p.y == y),
            self.points)

        # Maybe exhausted all points
        if len(valid_points) < 1:
            return None

        distances = map(lambda p: dist(x, y, p.x, p.y), valid_points)
        return valid_points[distances.index(min(distances))]

    def _did_miss_points(self, x, y):
        """
        Check if any points were passed when
        moving to this coord.
        """
        self.visited.add(Point(x, y))
        if not ((self._nothing_before(x, y) and
                self._mutually_exclusive_row_col(x, y))):
            return True

        nearest = self._get_nearest(x, y)

        # Did not visit all yet couldn't find nearest
        diffs = len(set(self.points) - self.visited)
        if (nearest is None and diffs > 0):
            return True
        elif nearest is None and diffs <= 0:
            return False
        elif nearest is not None and diffs > 0:
            return self._did_miss_points(nearest.x, nearest.y)
        else:
            raise RuntimeError(
                "There is an error in my logic. I have found that there"
                "exists another valid point, yet I have visited all points.")

    @property
    def is_possible(self):
        """
        Check if it is possible to traverse through
        all the Xs in a grid.

        A grid is possible if:
        - Starting on the bottom left most X, no other Xs exist
          on either the same row or column. All other Xs must exist
          only on the same row or column, never both.
        - No other X must exist on the row/col before the current X's
          row/col except for any previously visited ones.
        """
        if self._is_possible is None:
            x, y = self.start.coords
            self._is_possible = not self._did_miss_points(x, y)
        return self._is_possible


class Subgrid(Grid):
    """
    Class to replicate a grid where there exist only 2 Xs
    in the top right and bottom left areas of the grid.
    """

    def __init__(self, grid):
        super(Subgrid, self).__init__(grid)
        assert len(self.points) == 2

        self._paths = None

    @classmethod
    def from_points(cls, grid, start, end):
        """
        Get a subgrid where start and end are the opposite corners inclusively.
        """
        grid_ = []
        for y in xrange(len(grid)):
            if y <= start.y and y >= end.y:
                grid_.append(grid[y][start.x: end.x + 1])
        return cls(grid_)

    @property
    def paths(self):
        if self._paths is None:
            self._paths = self._move(self.start.x, self.start.y, [])
        return self._paths

    def _move(self, x, y, recording_path=None):
        """
        Move in up to 3 directions given a possible coord.
        return:
            List of the full paths taken from start to end.
        """
        recording_path = recording_path or []
        recording_path.append(Point(x, y))
        p1 = []
        p2 = []
        p3 = []
        if x < self.end.x:
            p1 = self._move(x + 1, y, recording_path=recording_path)
        if y > self.end.y:
            p2 = self._move(x, y - 1, recording_path=recording_path)
        if x < self.end.x and y > self.end.y:
            p3 = self._move(x + 1, y - 1, recording_path=recording_path)

        # The stopping condition is that all 3 are None since
        # we have already reached the end point.
        # Otherwise, p1, p2, or p3 may all be lists containing
        # recorded paths as elements.
        if p1 == p2 == p3 == []:
            return [recording_path]

        assert all(map(lambda x: isinstance(x, list), (p1, p2, p3, )))
        return p1 + p2 + p3


def main():
    # We know:
    # - There exists only 1 nearest point to the current point.
    #   - We can just find each sub grid with only 2 Xs and find
    #     the product of all the paths in each one.
    grid = Grid.from_stdin()

    if not grid.is_possible:
        print("<invalid input>")
        return 1
    print(grid.paths_count)

    return 0


if __name__ == "__main__":
    sys.exit(main())
