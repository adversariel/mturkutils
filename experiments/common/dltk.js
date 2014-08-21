/*!
 * dicarlo lab javascript toolkit
 */

(function (dltk, window) {
    /*************************************************************************
     * Common variables / constants                                          *
     *************************************************************************/
    dltk.STATLEN = 2;
    dltk.SLOPPY = 5;
    dltk.EPS = 2;                     // some slack time in ms for setTimeout2
    dltk.JS_TRES_TOL = 17;            // ~60Hz frame rate
    dltk.JS_TRES_VAR_TOL = 17 * 17;   // +/- one frame deviation deemed fine

    dltk.js_tres = null;              // setTimeout resolution
    dltk.js_tres_variance = null;
    dltk.bogoMIPS = null;

    var document = window.document;
    var performance = window.performance;


    /*************************************************************************
     * Utility functions                                                     *
     *************************************************************************/
    dltk.shuffle = function shuffle(o) {
        for (var j, x, i = o.length; i; j = parseInt(Math.random() * i, 10), x =
            o[--i], o[i] = o[j], o[j] = x);
        return o;
    };

    dltk.getURLParameter = function getURLParameter(name) {
        name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
        var regexS = "[\\?&]" + name + "=([^&#]*)";
        var regex = new RegExp(regexS);
        var results = regex.exec(window.location.href);
        if (results === null) return "";
        else return results[1];
    };


    /*************************************************************************
     * Timing/performance measurement functions                              *
     *************************************************************************/
    dltk.measureTimeResolution = function measureTimeResolution(callback, duration) {
        // Measures the minimum time resolution that can be attained by
        // regular setTimeout(fn, 0);
        // from: http://javascript.info/tutorial/events-and-timing-depth#javascript-is-single-threaded
        var i = 0;
        var sum_diff = 0, mean_diff;
        var sum_sq_diff = 0;
        var d = performance.now();
        var DUR_DEFAULT = 400;   // run for 400 counts by default
        var DUR = ((typeof(duration) == 'undefined') ? DUR_DEFAULT : duration);

        setTimeout(function measureTimeResolution_inner() {
            var diff = performance.now() - d;
            sum_diff += diff;
            sum_sq_diff += diff * diff;
            if (i++ == DUR) {
                // done calculating js time resolution
                mean_diff = sum_diff / i;
                dltk.js_tres = Math.max(mean_diff, 0);
                dltk.js_tres_variance = sum_sq_diff / i - mean_diff * mean_diff;
                if (typeof(callback) == 'function') callback(dltk.js_tres, dltk.js_tres_variance);
            }
            else {
                setTimeout(measureTimeResolution_inner, 0);
            }
            d = performance.now();
        }, 0);
    };

    dltk.setTimeout2Cnt = 0;
    dltk.setTimeout2 = function setTimeout2(fn, delay) {
        // A function similar to setTimeout but much more accurate
        var t0 = performance.now(), sloppy_delay;
        var setTimeout2_inner = function setTimeout2_inner() {
            while(performance.now() - t0 < delay - dltk.EPS) dltk.setTimeout2Cnt++;
            fn();
        };
        dltk.setTimeout2Cnt = 0;
        if (dltk.js_tres !== null)
            sloppy_delay = delay - dltk.js_tres * dltk.SLOPPY;
        else
            sloppy_delay = delay;

        if (sloppy_delay <= 0) setTimeout2_inner();
        else setTimeout(setTimeout2_inner, sloppy_delay);
    };

    dltk.getDriftCompensation = function getDriftCompensation(time_spent, prev_biases, ref) {
        // Simple function that estimates obtimal bias to attain time delay of "ref"
        // based on previously measured history of "time_spent" and "prev_biases"
        return time_spent.length >= dltk.STATLEN ? time_spent.mean() + prev_biases.mean() - ref : 0;
    };

    dltk.measureBogoMIPSOnce = function measureBogoMIPSOnce(duration) {
        // Measures BogoMIPS just once
        // from: http://www.pothoven.net/javascripts/src/jsBogoMips.js
        var t0 = performance.now();
        var loops_per_sec = 0 + 0;
        var t1 = performance.now();
        var compensation = t1 - t0;
        var DUR_DEFAULT = 500;   // run for 500ms by default
        var DUR = ((typeof(duration) == 'undefined') ? DUR_DEFAULT : duration);
        var tend = performance.now() + DUR;

        while (t1 < tend) {
            loops_per_sec++;
            t1 = performance.now();
        }

        return (loops_per_sec + (loops_per_sec * compensation)) / (1000000 / (1000 / DUR));
    };

    dltk.measureBogoMIPS = function measureBogoMIPS(callback, reps) {
        // Measures more accurate BogoMIPS by making several measurements
        var meas = [];
        var cnt = 0;
        var REPS_DEFAULT = 4;
        var REPS = ((typeof(reps) == 'undefined') ? REPS_DEFAULT : reps);

        var measureBogoMIPS_inner = function measureBogoMIPS() {
            meas.push(dltk.measureBogoMIPSOnce());
            cnt++;

            if (cnt < REPS) {
                setTimeout(measureBogoMIPS, 0);
                return;
            }

            dltk.bogoMIPS = meas.mean();
            if (typeof(callback) == 'function') callback(dltk.bogoMIPS);
        };
        measureBogoMIPS_inner();
    };

    /*************************************************************************
     * Graphics functions                                                    *
     *************************************************************************/
    dltk.getContextsFromCanvas = function getContextsFromCanvas(onscr_canvas_id) {
        // double buffering. from: http://blog.bob.sh/2012/12/double-buffering-with-html-5-canvas.html
        var mainCanvas = document.getElementById(onscr_canvas_id);
        var ctxMain = mainCanvas.getContext('2d');
        var ctxOffscreen = dltk.getOffscreenContext(mainCanvas.width, mainCanvas.height);

        return {onscr: ctxMain, offscr: ctxOffscreen};
    };

    dltk.getOffscreenContext = function getOffscreenContext(w, h) {
        var offscreenCanvas = document.createElement('canvas');
        if (typeof(w) == 'number') offscreenCanvas.width = parseInt(w);
        if (typeof(h) == 'number') offscreenCanvas.height = parseInt(h);
        return offscreenCanvas.getContext('2d');
    };

    dltk.drawToContext = function drawToContext(imgurl, ctx, callback, wrap) {
        // from: https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Canvas_tutorial/Using_images
        var img;
        var t_draw_begin = performance.now();
        img =  new Image();
        img.onload = function(){
            ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height);  // should stretch
            //ctx.drawImage(img, 0, 0);

            // if callback is requested...
            if (typeof(callback) == 'function') {
                if (wrap) {
                    setTimeout(callback, 0);
                }
                else callback();
            }
        };
        img.src = imgurl;
        return t_draw_begin;
    };

    dltk.copyContexts = function copyContexts(ctxsrc, ctxdst) {
        ctxdst.drawImage(ctxsrc.canvas, 0, 0);
    };


    /*************************************************************************
     * Functions to be exported immediately                                  *
     *************************************************************************/
    window.Array.prototype.flatten = function flatten() {
        var flat = [];
        for (var i = 0, l = this.length; i < l; i++) {
            var type = Object.prototype.toString.call(this[i]).split(' ').pop()
                .split(']').shift().toLowerCase();
            if (type) {
                flat = flat.concat(/^(array|collection|arguments|object)$/.test(
                    type) ? flatten.call(this[i]) : this[i]);
            }
        }
        return flat;
    };

    window.Array.prototype.getUnique = function() {
        var u = {},
            a = [];
        for (var i = 0, l = this.length; i < l; ++i) {
            if (u.hasOwnProperty(this[i])) {
                continue;
            }
            a.push(this[i]);
            u[this[i]] = 1;
        }
        return a;
    };

    window.Array.prototype.mean = function () {
        var sum = 0, j = 0; 
        for (var i = 0; i < this.length, isFinite(this[i]); i++) { 
            sum += parseFloat(this[i]); ++j; 
        } 
        return j ? sum / j : 0; 
    };

    window.Array.prototype.variance = function () {
        var sum = 0, j = 0, a; 
        for (var i = 0; i < this.length, isFinite(this[i]); i++) { 
            a = parseFloat(this[i]); ++j;
            sum += a * a; 
        } 
        a = this.mean();
        return j ? sum / j - a * a : 0; 
    };

}(window.dltk = window.dltk || {}, window));
