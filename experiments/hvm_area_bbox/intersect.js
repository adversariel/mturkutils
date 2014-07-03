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


    if ((minx <== xint) & (xint <== maxx) & (miny <== yint <== maxy)){
        return [[xint, yint]]
    } else {
        return []
    }

}


function pointirect(p, r) {
    if ($.inArray(p, r) > 0){
        return true
    }

    var ctr = center(r);
    var line0 = new Array(p, ctr);
    var lines = get_lines(r);
    var cintersects = _.each(function (l){return line_intersections(line0, l)},
                             lines);
    var clist = _.pluck(cintersects, 'length');
    var csum = _.reduce(clist, function(memo, num){ return memo + num; }, 0);
    if (csum === 0){
        return true
    } else {
        return false
    }

}


function get_lines(r){
    r = counterclockwise(r);
    return [[r[0], r[1]], [r[1], r[2]], [r[2], r[3]], [r[3], r[0]]]
}


function center(points){
    var a, b = _.zip.apply(_, points);
    a = _.reduce(a, function(memo, num){ return memo + num; }, 0) / a.length;
    b = _.reduce(b, function(memo, num){ return memo + num; }, 0) / b.length;
    return [a, b]
}


function counterclockwise(points){
    var ctr = center(points);
    var above = _.filter(points, function(p) {if (p[1] >= ctr[1]) {return true} else {false}});
    var below = _.filter(points, function(p) {if (p[1] < ctr[1]) {return true} else {false}})
}
