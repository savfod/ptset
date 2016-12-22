from line import Line

CONVEXITY_COEFFICIENT = 2  # coef for speed in edge points in bezier curve.
INTERPOLATED_POINTS_COUNT = 10


class LinearInterpolation:
    def __init__(self, points, index, closed):
        self.start_point = points[index]
        next_index = (index + 1) % len(points)
        self.vector = points[next_index] - points[index]

    def get_point(self, t):
        # t=0 - left point, t=1 - right point
        return self.start_point + self.vector.coeff_prod(t)

    def get_tangent(self, t):
        return self.vector


class SplineInterpolation:
    # generates smooth curve with power 3 by fixing tangent in p_i,
    # tangent is generated using p_{i-1} and p_{i+1}
    @staticmethod
    def gen_tangent(p0, p1, p2):
        p1_tangent = (p1-p0) * abs(p2-p1) + (p2-p1) * abs(p1-p0)
        p1_tangent /= (abs(p2-p1) + abs(p1-p0))
        p1_tangent /= CONVEXITY_COEFFICIENT
        return p1_tangent

    def __init__(self, points, index, closed):
        prev_p = points[index-1] if (index > 0 or closed) else points[index]
        used_p1 = points[index]
        used_p2 = points[(index+1) % len(points)]

        next_p = used_p2
        if ((index+2 < len(points)) or closed):
            next_p = points[(index+2) % len(points)]

        self.p0 = used_p1
        self.p1 = used_p1 \
            + SplineInterpolation.gen_tangent(prev_p, used_p1, used_p2)
        self.p2 = used_p2 \
            - SplineInterpolation.gen_tangent(used_p1, used_p2, next_p)
        self.p3 = used_p2

    def get_point(self, t):
        # t=0 - left point, t=1 - right point
        return self.p0 * ((1-t)**3) + \
               self.p1 * (3 * t * (1-t)**2) + \
               self.p2 * (3 * (t**2) * (1-t)) + \
               self.p3 * (t**3)

    def get_tangent(self, t):
        return Line(
            self.get_point(t),

            self.p0 * (-3 * (1-t)**2) +
            self.p1 * (3 * (1-t) * (1-3*t)) +
            self.p2 * (3 * t * (2-3*t)) +
            self.p3 * (3 * t**2)
        )


class Curve:
    def __init__(self, points, closed=False):
        self.points = points
        self.closed = closed
        self.make_interpolation()

    def make_interpolation(self):
        self.interpolations = []
        self.interpolated_points = []

        if len(self.points) < 2:
            return

        max_ind = len(self.points) if self.closed else len(self.points) - 1
        for ind in range(max_ind):
            self.interpolated_points.append(self.points[ind])
            interpolation = SplineInterpolation(self.points, ind, self.closed)

            self.interpolations.append(interpolation)
            for i in range(INTERPOLATED_POINTS_COUNT):
                t = (1 + i) / (INTERPOLATED_POINTS_COUNT + 1.)
                self.interpolated_points.append(interpolation.get_point(t))
        if not self.closed:
            self.interpolated_points.append(self.points[-1])

    def get_all_points(self):
        points = self.interpolated_points[:]
        if self.closed:
            points += [self.points[0]]
        return points

    def find_intersection_intervals(self, line):
        max_ind = len(self.points) if self.closed else len(self.points) - 1
        intervals_ind = []
        for i in range(max_ind):
            p1 = self.points[i]
            p2 = self.points[(i+1) % len(self.points)]
            if line.diff_side_of_line(p1, p2):
                intervals_ind.append(i)
        return intervals_ind

    @staticmethod
    def find_point(interpolation, line):
        left_point = interpolation.get_point(0)
        left = 0.
        right = 1.
        for i in range(10):
            middle = (left + right) / 2
            mid_point = interpolation.get_point(middle)
            if line.diff_side_of_line(left_point, mid_point):
                right = middle
            else:
                left = middle
        return (left + right) / 2

    def find_intersections(self, line):
        points = []
        intervals = self.find_intersection_intervals(line)
        for i in intervals:
            ip = self.interpolations[i]
            t = Curve.find_point(ip, line)
            points.append(ip.get_point(t))
        return points

    def find_intersections_tangents(self, line):
        tangents = []
        intervals = self.find_intersection_intervals(line)
        for i in intervals:
            ip = self.interpolations[i]
            t = Curve.find_point(ip, line)
            tangents.append(ip.get_tangent(t))
        return tangents
