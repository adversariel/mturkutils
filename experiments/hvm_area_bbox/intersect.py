import math
import numpy as np

def line_intersections(l1, l2):
    if l1[1][0] == l1[0][0]:
        slope1 = None
    else:
        slope1 = (l1[1][1] - l1[0][1]) / (l1[1][0] - l1[0][0])

    if l2[1][0] == l2[0][0]:
        slope2 = None
    else:
        slope2 = (l2[1][1] - l2[0][1]) / (l2[1][0] - l2[0][0])

    if slope1 == slope2:
        return []
    else:
        if slope1 is None:
            b2 = l2[0][1] - slope2 * l2[0][0]
            xint = l1[0][0]
            yint = slope2 * xint + b2
        elif slope2 is None:
            b1 = l1[0][1] - slope1 * l1[0][0]
            xint = l2[0][0]
            yint = slope1 * xint + b1
        else:
            b1 = l1[0][1] - slope1 * l1[0][0]
            b2 = l2[0][1] - slope2 * l2[0][0]
            xint = (b2 - b1) / (slope1 - slope2)
            yint = slope1 * xint +  b1

        minx1 = min(l1[0][0], l1[1][0])
        maxx1 = max(l1[0][0], l1[1][0])
        miny1 = min(l1[0][1], l1[1][1])
        maxy1 = max(l1[0][1], l1[1][1])
        minx2 = min(l2[0][0], l2[1][0])
        maxx2 = max(l2[0][0], l2[1][0])
        miny2 = min(l2[0][1], l2[1][1])
        maxy2 = max(l2[0][1], l2[1][1])

        if (minx1 <= xint <= maxx1) and (miny1 <= yint <= maxy1) and (minx2 <= xint <= maxx2) and (miny2 <= yint <= maxy2):
            return [(xint, yint)]
        return []


def pointinrect(p, r):
    if p in r:
        return True
    ctr = center(r)
    line0 = (p, ctr)
    lines = get_lines(r)
    cintersects = [line_intersections(line0, l) for l in lines]
    clist = map(len, cintersects)
    csum = sum(clist)
    assert 0 <= csum <= 2, (p, clist, lines)
    return (csum == 0)


def get_lines(r):
    r = counterclockwise(r)
    return [(r[0], r[1]),
            (r[1], r[2]),
            (r[2], r[3]),
            (r[3], r[0])]


def center(points):
    a, b = zip(*points)
    return (np.mean(a), np.mean(b))


def counterclockwise(points):
    ctr = center(points)
    above = [p for p in points if p[1] > ctr[1]]
    below = [p for p in points if p[1] <= ctr[1]]
    distsabove = [math.sqrt((p[0] - ctr[0])**2 + (p[1] - ctr[1])**2) for p in above]
    cosesabove = np.array([(p[0] - ctr[0]) / d for p, d in zip(above, distsabove)])
    distsbelow = [math.sqrt((p[0] - ctr[0])**2 + (p[1] - ctr[1])**2) for p in below]
    cosesbelow = np.array([(p[0] - ctr[0]) / d for p, d in zip(below, distsbelow)])
    return [above[i] for i in cosesabove.argsort()[::-1]] + \
           [below[i] for i in cosesbelow.argsort()]


def get_convex_area(points):
    n = len(points)
    t1 = sum([points[i][0] * points[(i+1) % n][1] for i in range(n)])
    t2 = sum([points[i][1] * points[(i+1) % n][0] for i in range(n)])
    return 0.5 * (t1 - t2)


def intersection_area(r1, r2):
    r1 = [(float(a), float(b)) for (a,b) in r1]
    r2 = [(float(a), float(b)) for (a,b) in r2]
    lines1 = get_lines(r1)
    lines2 = get_lines(r2)

    intersections = []
    for l1 in lines1:
        for l2 in lines2:
            li = line_intersections(l1, l2)
            intersections.extend(li)

    inpoints = []
    for p1 in r1:
        if pointinrect(p1, r2):
            inpoints.append(p1)
    for p2 in r2:
        if pointinrect(p2, r1):
            inpoints.append(p2)

    ppoints = list(set(intersections + inpoints))
    ppoints = counterclockwise(ppoints)
    if len(ppoints) > 2:
        area = get_convex_area(ppoints)
    else:
        area = 0
    return area

