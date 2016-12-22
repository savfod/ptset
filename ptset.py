#!/usr/bin/python3

DESCRIPTION = '''

Program for ptset drawing. 

Some examples of usage: 
python ptset.py -h 
python ptset.py --curve 9 --draw_points A,0.199,True B,0.412,True 
python ptset.py --curve 8 --draw_points A,-0.36,True X1,-0.26 B,0,True X2,0.26 C,0.36,True
python ptset.py --curve 7 --tangent_curve
python ptset.py --curve 4 --points_count 50



'''


from vec import Vec
from line import Line
from curve import Curve
from drawer import Drawer

import argparse
import math
import random
import sys


RADIUS = 2
RAD_ADD = 3
COUNT = None # getting from params
START_X = -1
FINISH_X = 1

FILL1 = "green"
FILL2 = "blue"
FILL3 = "red"


drawer = None  # useful for debugging
DRAW_POINTS = []  # getting from params
POINTS_MULTIPLIER = 1000 

def init_tk_drawer():
    global drawer
    drawer = Drawer()

    return drawer.tk, drawer


def vertical_line(x):
    return Line(Vec(x, 0), Vec(0, 1))


class Interface:
    def __init__(self, drawer, function, tangent_function=None):
        self.drawer = drawer
        self.function = function
        self.tangent_function = tangent_function
        self.prev_points = {"tang_point":None, "tang_pair_point":None}

        self.current_index = 0

        self.to_remove = []

        points = []
        for i in range(COUNT):
            x = START_X + (FINISH_X-START_X)*i/float(COUNT-1)
            y = function(x)
            points.append(Vec(x,y))
        self.curve = Curve(points, closed=False)
        self.drawer.draw_curve(self.curve, fill=FILL1)

        semiplane = []
        HOR_COUNT = COUNT * 2
        def i_to_x(i):
            return START_X + (FINISH_X-START_X)*i/float(HOR_COUNT-1)
        def j_to_x(j):
            return START_X + (FINISH_X-START_X)*j/float(VER_COUNT-1)
        VER_COUNT = COUNT * 2
        for j in range(VER_COUNT):
            semiplane.append([])
            px = j_to_x(j)
            px_line = vertical_line(px)

            for i in range(HOR_COUNT):
                tx = i_to_x(i)
                ty = function(tx)
                T = Vec(tx, ty)
                dx = 0.001
                der = (function(tx + dx) - function(tx - dx))/(2 * dx)
                tangent = Line(T, Vec(1, der))



                t_value = px_line.intersect(tangent).y
                t_value_2 = ty + der * (px - tx)
                # print(t_value, t_value_2)

                semiplane_value = self.function(px) < t_value
                semiplane[-1].append(semiplane_value)

                # self.drawer.draw_circle(Vec(px,tx), r=1, img_index=1)

        #draw edges
        def draw_edge(i1, i2, j1, j2):
            def to_vec(i, j):
                return Vec(i_to_x(i), j_to_x(j))
            self.drawer.draw_line(to_vec(i1, j1), to_vec(i2, j2), fill=FILL2, img_index=2, width=2)
            self.drawer.draw_line(to_vec(i1, j1), to_vec(i2, j2), fill=FILL2, img_index=3, width=2)

        for i in range(VER_COUNT - 1):
            for j in range(HOR_COUNT - 1):
                four_value = (
                    semiplane[i][j],
                    semiplane[i+1][j],
                    semiplane[i][j+1],
                    semiplane[i+1][j+1]
                )

                #horizontal_edges
                if four_value == (True, True, False, False):
                    draw_edge(i, i+1, j, j)
                elif four_value == (False, False, True, True):
                    draw_edge(i, i+1, j+1, j+1)

                #vertical_edges
                elif four_value == (True, False, True, False):
                    draw_edge(i, i, j, j+1)
                elif four_value == (False, True, False, True):
                    draw_edge(i+1, i+1, j, j+1)

                #diagonal_edge
                else:
                    d1 = four_value[0], four_value[3]
                    d2 = four_value[1], four_value[2]
                    if d1 == (True, True) and False in d2:
                        draw_edge(i, i+1, j, j+1)
                    elif d2 == (True, True) and False in d1:
                        draw_edge(i, i+1, j+1, j)

        DIAG_COUNT = COUNT // 5
        def diag_x(i):
            return START_X + (FINISH_X-START_X)*i/float(DIAG_COUNT-1)
        for i in range(DIAG_COUNT):
            x1 = diag_x(i)
            x2 = diag_x(i+1)
            self.drawer.draw_line(Vec(x1, x1), Vec(x2, x2), width=3, fill=FILL1, img_index=2)
            self.drawer.draw_line(Vec(x1, x1), Vec(x2, x2), width=3, fill=FILL1, img_index=3)


        self.points = []
        self.is_drawing = True
        self.selected_point = None

        self.tangent_points = self.calc_tangent_points(function)

        # for x in [-0.65, -0.45, -0.25, -0.05]:
        #     x -= 0.02
        #     self.drawer.draw_line(Vec(x, 0.2), Vec(x, 0.4), img_index=2, fill=FILL3, width=1)

    def calc_tangent_points(self, function):
        DIFF = 0.1

        max_skip = (FINISH_X - START_X)*3 / float(POINTS_MULTIPLIER*COUNT)
        average_skip = (FINISH_X - START_X) / float(POINTS_MULTIPLIER*COUNT)
        min_skip = (FINISH_X - START_X) / float(5*POINTS_MULTIPLIER*COUNT)

        points = [START_X]
        while points[-1] < FINISH_X:
            x = points[-1]
            der2 = (function(x - DIFF) + function(x + DIFF) - 2*function(x)) / DIFF**2
            skip = 100 * average_skip / (abs(der2)**2 + 0.00001)

            # if min_skip < skip < max_skip:
            #     print ("Success") #DEBUG. TO CALC GOOD COEFFICIENT
            # else:
            #     if min_skip < skip:
            #         print("Small")
            #     else:
            #         print("Big")

            skip = min(skip, max_skip)
            skip = max(min_skip, skip)

            points.append(x + skip)
        return points

    def draw_point(self, x, label, with_tangent=False):
        l = vertical_line(x)
        points = self.curve.find_intersections(l)
        p = points[0]
        tangents = self.curve.find_intersections_tangents(l)
        t = tangents[0]

        self.drawer.draw_circle(p, fill=FILL2, label=label)

        if with_tangent:
            self.drawer.draw_line(t.start - t.vec*(10/abs(t.vec)), t.start + t.vec*(10/abs(t.vec)), dash=[8,4])

            self.drawer.draw_line(Vec(p.x, p.x) - Vec(10,0), Vec(p.x, p.x) + Vec(10,0) , img_index=2, dash=[8,4])
            self.drawer.draw_circle(Vec(p.x, p.x), fill=FILL2, img_index=2, label=label)


    def draw_pic(self):
        self.is_drawing = True
        self.drawer.tk.after(10, self.draw_pic_iteration)

        def parse_str(s):
            try:
                parts = s.strip().split(",")
                if len(parts) == 2:
                    parts = parts + [""] # bool("") == False

                return parts[0].strip(), float(parts[1]), bool(parts[2])
            except:
                raise ValueError('Not expected point params. Expected string in format x_coordinate,label[,draw_tangent]. E.g. "A,0" or "B,-0.5,True")')

        if DRAW_POINTS:
            for s in DRAW_POINTS:
                label, x, with_tangent = parse_str(s)
                self.draw_point(x, label, with_tangent)


    def image2(self, vec):
        return Vec(vec.x + 2, vec.y)

    def draw_pic_iteration(self):
        self.drawer.remove_tmp()

        if self.current_index + 1 < len(self.tangent_points):
            self.current_index += 1
        else:
            self.current_index = 0
            for k in self.prev_points.keys():
                self.prev_points[k] = None

        i = self.current_index
        skip = self.tangent_points[i+1] - self.tangent_points[i] if i+1 < len(self.tangent_points) else  self.tangent_points[i] - self.tangent_points[i-1]
        x = self.tangent_points[i] + random.random()*skip
        # print("iteration, x=", x)

        l = vertical_line(x)
        self.drawer.draw_line(Vec(START_X,x), Vec(FINISH_X,x), tmp_object=True, img_index=2)


        tangents = self.curve.find_intersections_tangents(l)
        points = self.curve.find_intersections(l)


        if len(tangents) == 1:
            self.drawer.draw_line(tangents[0].start - tangents[0].vec*(10/abs(tangents[0].vec)), tangents[0].start + tangents[0].vec*(10/abs(tangents[0].vec)), tmp_object=True)
            self.drawer.draw_circle(points[0], r=RAD_ADD+RADIUS, fill=FILL1, tmp_object=True)

            points = self.curve.find_intersections(tangents[0])

            for (ind,p) in enumerate(points):
                self.drawer.draw_circle(p, r=RAD_ADD+ind+RADIUS, fill=FILL2, tmp_object=True)
                # self.drawer.draw_circle(Vec(p.x, x), img_index=2)
                # self.drawer.draw_circle(Vec(p.x, x), img_index=3)
                self.drawer.draw_circle(Vec(p.x, x), r=(RAD_ADD+ind)+RADIUS, fill=FILL2, img_index=2, tmp_object=True)
                self.drawer.draw_circle(Vec(p.x, x), r=(RAD_ADD+ind)+RADIUS, fill=FILL2, img_index=3, tmp_object=True)

            if self.tangent_function:
                l2 = vertical_line(self.tangent_function(x))
                tang_p = tangents[0].intersect(l2)
                self.drawer.draw_circle(Vec(tang_p.x, x), r=2*RADIUS, fill=FILL3, img_index=2, tmp_object=True)
                self.drawer.draw_circle(Vec(tang_p.x, x), r=2*RADIUS, fill=FILL3, img_index=3, tmp_object=True)
                #self.drawer.draw_circle(Vec(tang_p.x, x), r=RADIUS//2, fill=FILL3, img_index=2)
                if self.prev_points["tang_pair_point"]:
                    self.drawer.draw_line(self.prev_points["tang_pair_point"], Vec(tang_p.x, x), fill=FILL3, img_index=2)
                self.prev_points["tang_pair_point"] = Vec(tang_p.x, x)



                self.drawer.draw_circle(tang_p, r=2*RADIUS, fill=FILL3, tmp_object=True)
                # self.drawer.draw_circle(tang_p, r=RADIUS//2, fill=FILL3)
                if self.prev_points["tang_point"]:
                    self.drawer.draw_line(self.prev_points["tang_point"], tang_p, fill=FILL3)
                self.prev_points["tang_point"] = Vec(tang_p.x, tang_p.y)



        else:
            #print(x, len(tangents), len(points))
            pass

        self.drawer.draw_circle(Vec(x,x), r=RAD_ADD+RADIUS, fill=FILL1, img_index=2, tmp_object=True)
        self.drawer.draw_circle(Vec(x,x), r=RAD_ADD+RADIUS, fill=FILL1, img_index=3, tmp_object=True)
        # self.drawer.draw_circle(Vec(x,x), fill=FILL1, img_index=2)
        # self.drawer.draw_circle(Vec(x,x), fill=FILL1, img_index=3)


        if self.is_drawing:
            self.drawer.tk.after(10, self.draw_pic_iteration)

        # for v in self.drawer.canvases.values():
        #     v.update_idletasks()


    def start_drawing(self, event):
        self.is_drawing = True
        self.draw_pic()
        # self.add_point(event.x, event.y)

    def stop_drawing(self, event):
        self.is_drawing = False

    def remove_tmp(self):
        self.is_drawing = False
        self.drawer.remove_tmp()

    def zoom(self, event):
        print("Hello windows/macos! Not-tested scaling.")
        self.drawer.scale(1.1 ** event.delta, event.x, event.y)

    def zoom_in(self, event):
        self.drawer.scale(1.1, event.x, event.y)

    def zoom_out(self, event):
        self.drawer.scale(1.1 ** (-1), event.x, event.y)

def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION,
    )
    # parser.add_argument('--rounds', type=int, default=2, help='how many rounds each pair plays')
    parser.add_argument('--curve', type=int, default="9", help='curve funciton index')
    parser.add_argument('--points_multiplier', type=int, default="2", help='how many points to use')
    parser.add_argument('--tangent_curve', action="store_true", help='draw tangent curve')
    parser.add_argument('--points_count', type=int, default=180, help='how many points to use (more points is slower)')
    # parser.add_argument('--cyclic', action="store_true", default="False", help='draw tangent curve')
    # parser.add_argument('--draw_points', action="store_true", default=False, help='draw selected points')
    parser.add_argument('--draw_points', nargs="+", help='draw selected points. format: x_coordinate,label[,draw_tangent]')
    parsed_args = parser.parse_args()

    global POINTS_MULTIPLIER
    POINTS_MULTIPLIER = parsed_args.points_multiplier

    global DRAW_POINTS
    DRAW_POINTS = parsed_args.draw_points
    
    global COUNT
    COUNT = parsed_args.points_count


    return parsed_args


def func(x, ind=9):
    # several types of prepared functions
    x *= 2
    if ind == 1:
        return (x**6 - 5*x**4 + 6*x**2 - 1)/2
    elif ind == 2:
        return (x**6 - 5*x**4 + 6*x**2 - 1)/2/(1 + (2*x)**8)
    elif ind == 3:
        return (128*x**8 - 256*x**6 + 160*x**4 - 32*x**2 + 1)
    elif ind == 4:
        return (128*x**8 - 256*x**6 + 160*x**4 - 32*x**2 + 1)/(1 + 128*x**12)
    elif ind == 5:
        return (x**6 - 5*x**4 + 6*x**2 - 1)/2
    elif ind == 6:
        x = 1.3*x
        return (15*x**5 - 29*x**3 + 7*x)/(3 + 30*x**10) + 0.01
    elif ind == 7:
        return (x**3 - x) / (10*x**4 + 1)
    elif ind == 8:
        return (x) / (10*x**6 + 1) + 0.01
    elif ind == 9:
        # special curve with isolated closed curves in ptset
        x *= 10
        x += 2

        x1 = x + 8
        x2 = x - 8
        x3 = x2 + 3.5

        res = 1/(0.01*x1**6 + 0.03*x1**2 + 0.8) \
            - 1/(0.01*x2**6 - 0.01*(x3)**2 + 0.8) \
            - 0.04
        return res / 2
    elif ind == 10:
        x = 2*x
        return (x)/(0.1*x**6 + 0.8) - x/(10*x**2 + 1) + 0.01
    else:
        raise ValueError("no function with such index")


def main():
    args = parse_args()
    tk, drawer = init_tk_drawer()

    def function(x):
        return func(x, args.curve)
    tang_func = (lambda x: x+2/(100*x**2 + 4)) if args.tangent_curve else None
    interface = Interface(drawer, function, tang_func)
    # interface.is_drawing = args.cyclic

    tk.bind("<Button-1>", interface.start_drawing)
    # tk.bind("<ButtonRelease-1>", interface.stop_drawing)
    # tk.bind("<Motion>", interface.draw)
    tk.bind("<ButtonRelease-2>", interface.stop_drawing)
    tk.bind("<ButtonRelease-3>", interface.stop_drawing)
    tk.bind("<MouseWheel>", interface.zoom)
    tk.bind("<Button-4>", interface.zoom_in)
    tk.bind("<Button-5>", interface.zoom_out)
    # tk.focus_set() #comment this line for image without (with pale) edge
    tk.bind("<Escape>", lambda x: interface.remove_tmp())

    tk.after(100, lambda: interface.start_drawing(None))
    tk.mainloop()


if __name__ == "__main__":
    main()
