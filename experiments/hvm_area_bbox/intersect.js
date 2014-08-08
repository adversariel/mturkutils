function line_intersections(l1, l2) {

    var slope1, slope2, b1, b2, xint, yint, minx, miny, maxx, maxy;

    if (l1[1][0] === l1[0][0]){
        slope1 = null;
    } else {
        slope1 = (l1[1][1] - l1[0][1]) / (l1[1][0] - l1[0][0]);
    }

    if (l2[1][0] === l2[0][0]){
        slope2 = null;
    } else {
        slope2 = (l2[1][1] - l2[0][1]) / (l2[1][0] - l2[0][0]);
    }

    if (slope1 === slope2){
        return []
    } else {
         if (slope1 === null){
            b2 = l2[0][1] - slope2 * l2[0][0]
            xint = l1[0][0]
            yint = slope2 * xint + b2
         } else if (slope2 === null) {
            b1 = l1[0][1] - slope1 * l1[0][0]
            xint = l2[0][0]
            yint = slope1 * xint + b1
         } else {
            b1 = l1[0][1] - slope1 * l1[0][0]
            b2 = l2[0][1] - slope2 * l2[0][0]
            xint = (b2 - b1) / (slope1 - slope2)
            yint = slope1 * xint +  b1
         }

        minx = Math.max(Math.min(l1[0][0], l1[1][0]),
                        Math.min(l2[0][0], l2[1][0]));
        maxx = Math.min(Math.max(l1[0][0], l1[1][0]),
                        Math.max(l2[0][0], l2[1][0]));
        miny = Math.max(Math.min(l1[0][1], l1[1][1]),
                        Math.min(l2[0][1], l2[1][1]));
        maxy = Math.min(Math.max(l1[0][1], l1[1][1]),
                        Math.max(l2[0][1], l2[1][1]));
    }

    if ((minx <= xint) & (xint <= maxx) & (miny <= yint) & (yint <= maxy)){
        return [[xint, yint]]
    } else {
        return []
    }

}


function center(points){
    var _A = _.zip.apply(_, points);
    var a = _A[0];
    var b = _A[1];
    a = _.reduce(a, function(memo, num){ return memo + num; }, 0) / a.length;
    b = _.reduce(b, function(memo, num){ return memo + num; }, 0) / b.length;
    return [a, b]
}

function get_lines(r){
    r = counterclockwise(r);
    return [[r[0], r[1]], [r[1], r[2]], [r[2], r[3]], [r[3], r[0]]]
}


function InArray(x, Y){
    var str0 = JSON.stringify(x);
    var strings = _.map(Y, JSON.stringify);
    return $.inArray(str0, strings)
}

function pointinrect(p, r) {
    if (InArray(p, r) > -1){
        return true
    }
    var ctr = center(r);
    var line0 = [p, ctr];
    var lines = get_lines(r);
    var cintersects = _.map(lines, function(l){return line_intersections(line0, l);});
    var clist = _.pluck(cintersects, 'length');
    var csum = _.reduce(clist, function(memo, num){ return memo + num; }, 0);
    if (csum === 0){
        return true
    } else {
        return false
    }

}


function counterclockwise(points){
    var ctr = center(points);
    var above = _.filter(points, function(p) {if (p[1] >= ctr[1]) {return true} else {false}});
    var below = _.filter(points, function(p) {if (p[1] < ctr[1]) {return true} else {false}})
    function dfunc(p){return Math.sqrt(Math.pow(ctr[0]-[0], 2) + Math.pow(ctr[1] - p[1], 2))};
    var distsabove = _.map(above, dfunc);
    var distsbelow = _.map(below, dfunc);
    function cos(p){return (p[0] - ctr[0]) / dfunc(p)};
    var cosesabove = _.map(above, cos);
    var cosesbelow = _.map(below, cos);
    var above = _.sortBy(above, function(i){return cosesabove[above.indexOf(i)];}).reverse();
    var below = _.sortBy(below, function(i){return cosesbelow[below.indexOf(i)];});
    return above.concat(below)
}


function get_convex_area(points){
    points = counterclockwise(points);
    var n = points.length;
    var _A = _.zip.apply(_, points);
    var a1 = _A[0], a2 = _A[1];
    var t1 = _.map(_.range(n), function(i){return a1[i] * a2[(i+1) % n];});
    var t2 = _.map(_.range(n), function(i){return a2[i] * a1[(i+1) % n];});
    t1 = _.reduce(t1, function(memo, num){ return memo + num; }, 0);
    t2 = _.reduce(t2, function(memo, num){ return memo + num; }, 0);
    return 0.5 * (t1 - t2)
}


function intersection_area(r1, r2) {
    var lines1 = get_lines(r1);
    var lines2 = get_lines(r2);
    var intersections = [];
    var li, l1i, l2i;
    for (l1i=0; l1i < lines1.length; l1i++) {
        for (l2i=0; l2i < lines2.length; l2i++) {
            li = line_intersections(lines1[l1i], lines2[l2i]);
            intersections.push.apply(intersections, li);
        }
    }

    var inpoints = [];
    var p1i;
    for (p1i=0; p1i<r1.length; p1i++) {
        if (pointinrect(r1[p1i], r2)){
             inpoints.push(r1[p1i]);
        }
    }
    var p2i;
    for (p2i=0; p2i<r1.length; p2i++) {
        if (pointinrect(r2[p2i], r1)){
             inpoints.push(r2[p2i]);
        }
    }


    function uniqify(X){
        var i, res=[];
        for (i=0; i<X.length; i++){
            if (InArray(X[i], res) === -1){
                res.push(X[i]);
            }
        }
        return res
    }

    var ppoints = uniqify(intersections.concat(inpoints));
    if (ppoints.length > 2) {
        return get_convex_area(ppoints)
    } else {
        return 0
    }

}


