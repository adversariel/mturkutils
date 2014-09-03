/*!
 * dicarlo lab javascript toolkit
 */

(function (dltk, window) {
    /*************************************************************************
     * Common variables / constants                                          *
     *************************************************************************/
    dltk.STATLEN = 2;                 // minimum length to compute statistics
    dltk.SLOPPY = 5;                  // the amount of shortfall in setTimeout2
    dltk.EPS = 2;                     // slack time in setTimeout2
    dltk.JS_TRES_TOL = 17;            // An example tolerance value for js timing (~60Hz frame rate)
    dltk.JS_TRES_VAR_TOL = 17 * 17;   // +/- one frame deviation deemed fine
    dltk.STATLEN_FPS = 2;             // use last two fps to figure out current fps

    dltk.preloaded_rsrcs = {};        // a dictionary of on/off screen contexts + etc. for preloaded imgs

    dltk.js_tres = null;              // setTimeout resolution...
    dltk.js_tres_variance = null;     // ...and variance
    dltk.bogoMIPS = null;             // same as the name
    dltk.refresh_test_timestamps = null;

    dltk._jobs = [];                  // functions to be called sequentially and asynchronously

    var document = window.document;
    var performance = window.performance;
    /* //handle case in which performance is undefined (e.g. Safari)
    if (performance === undefined) {
        performance = {start: Date.now()};
        performance.now = function () {
            return Date.now() - performance.start;
        };
    };*/


    /*************************************************************************
     * Utility functions                                                     *
     *************************************************************************/
    var toMicrosec = function (x) { return parseInt(Math.round(x * 1000), 10); };

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

    dltk.wait = function wait(flags, callback, chkevery) {
        var chkinterval = defined(chkevery) ? parseInt(chkevery, 10) : 100;
        var wait_inner = function wait_inner() {
            var finished = true;
            for (var i = 0; i < flags.length; i++) {
                if (!flags[i]) finished = false;
            }

            if (finished) callback();
            else setTimeout(wait_inner, chkinterval);
        };
        setTimeout(wait_inner, chkinterval);
    };

    dltk.queueJob = function queueJob(fn) {
        // schedule a job to be run sequentially and asynchronously.
        // fn must be a function and should call dltk.runQueuedJobs() upon completion.
        dltk._jobs.push(fn);
    };

    dltk.runQueuedJobs = function runQueuedJobs() {
        var fn = dltk._jobs.splice(0, 1)[0];   // pops the current 0-th element
        if (callable(fn)) fn(performance.now());
    };

    dltk.getTimeSpent = function getTimeSpent(history) {
        // simplify the "history" format returned by dltk.queueTrial
        var j, tspent = [];
        for (var i = 0; i < history.length; i++) {
            j = history[i].length;
            if (j === 0) j = 1;  // avoid undefined
            tspent.push(history[i][j - 1] - history[i][0]);
        }
        return tspent;
    };

    dltk.getTimingHistoryExcerpt = function getTimingHistoryExcerpt(history, mode, center, nptsaround) {
        // Returns an excerpt of the timing history in us unit.  This is mainly used to reduce the
        // JSON string size of history.  Smaller JSON string of history could reduce the risk of
        // submission error upon task completion (of course, if history is included in the response data).
        // - mode (optional): sets the operation mode.  Possible options:
        //    - "default" : default operation.
        //    - "diff" : returns the differences between data points plus the initial time point
        var m = defined(mode) ? mode : 'default';
        var i_ctr = defined(center) ? center : 2;       // index to extract centrally
        var n = defined(nptsaround) ? nptsaround : 5;   // # of data points to collect around center
        var excerpt = [];
        var a;

        if (m == 'diff') {
            var tb = history.flatten()[0];   // the beginning time of this history
            a = history[i_ctr - 1].slice(-n);
            excerpt.push(toMicrosec(tb));
            excerpt.push(toMicrosec(a[0] - tb));  // offset relative to tb
            excerpt.push(a.diff().map(toMicrosec));
            excerpt.push(history[i_ctr].diff().map(toMicrosec));
            excerpt.push(history[i_ctr + 1].slice(0, n).diff().map(toMicrosec));
        }
        else if (m == 'diffeach') {
            a = history[i_ctr - 1].slice(-n);
            excerpt.push(toMicrosec(a[0]));
            excerpt.push(a.diff().map(toMicrosec));
            a = history[i_ctr];
            excerpt.push(toMicrosec(a[0]));
            excerpt.push(a.diff().map(toMicrosec));
            a = history[i_ctr + 1].slice(0, n);
            excerpt.push(toMicrosec(a[0]));
            excerpt.push(a.diff().map(toMicrosec));
        }
        else {   // default
            excerpt.push(history[i_ctr - 1].slice(-n).map(toMicrosec));
            excerpt.push(history[i_ctr].map(toMicrosec));
            excerpt.push(history[i_ctr + 1].slice(0, n).map(toMicrosec));
        }

        return excerpt;
    };

    var callable = function callable(obj) {
        return typeof(obj) == 'function';
    };

    var defined = function defined(obj) {
        return typeof(obj) != 'undefined';
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
        var DUR = (!defined(duration) ? DUR_DEFAULT : duration);

        setTimeout(function measureTimeResolution_inner() {
            var diff = performance.now() - d;
            sum_diff += diff;
            sum_sq_diff += diff * diff;
            if (i++ == DUR) {
                // done calculating js time resolution
                mean_diff = sum_diff / i;
                dltk.js_tres = Math.max(mean_diff, 0);
                dltk.js_tres_variance = sum_sq_diff / i - mean_diff * mean_diff;
                if (callable(callback)) callback(dltk.js_tres, dltk.js_tres_variance);
            }
            else {
                setTimeout(measureTimeResolution_inner, 0);
            }
            d = performance.now();
        }, 0);
    };

    dltk._setTimeout2Cnt = 0;  // debugging purposes only. do not rely on this variable.
    dltk.setTimeout2 = function setTimeout2(fn, delay) {
        // A function similar to setTimeout but much more accurate
        // NOTE: however this does NOT guarantee actual redrawing of the
        // screen by the browser.
        var t0 = performance.now(), sloppy_delay;
        var setTimeout2_inner = function setTimeout2_inner() {
            while(performance.now() - t0 < delay - dltk.EPS) dltk._setTimeout2Cnt++;
            fn();
        };
        dltk._setTimeout2Cnt = 0;
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
        var DUR = (!defined(duration) ? DUR_DEFAULT : duration);
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
        var REPS_DEFAULT = 3;
        var REPS = (!defined(reps) ? REPS_DEFAULT : reps);

        var measureBogoMIPS_inner = function measureBogoMIPS_inner() {
            if (cnt < REPS) {
                meas.push(dltk.measureBogoMIPSOnce());
                cnt++;
                setTimeout(measureBogoMIPS_inner, 0);
                return;
            }
            dltk.bogoMIPS = meas.mean();
            if (callable(callback)) callback(dltk.bogoMIPS);
        };
        measureBogoMIPS_inner();
    };

    dltk.measureScreenRefreshInterval = function measureScreenRefreshInterval(canvas, callback, test_color, reps) {
        var REPS_DEFAULT = 120;
        var REPS = (!defined(reps) ? REPS_DEFAULT : reps);
        var COLOR_DEFAULT = '#7f7f7f';
        var COLOR = (!defined(test_color) ? COLOR_DEFAULT : test_color);
        var timestamps = [];
        var ctx = dltk.getOnScreenContextFromCanvas(canvas);

        var measureScreenRefreshIntervals_inner = function measureScreenRefreshIntervals_inner(ts) {
            dltk.drawToContext('color:' + COLOR, ctx);
            timestamps.push(ts);

            if (timestamps.length >= REPS) {
                // finished testing
                dltk.refresh_test_timestamps = timestamps;
                if (callable(callback)) setTimeout(function() {
                    // this tries to detect bad states in browsers on Windows
                    // especially after the computer wakes up from a sleep.
                    // "Bad" timestamps are almost always exact multiples of 100us
                    // (and typically multiples of 1000us).
                    var isquantized = function (x) { return (toMicrosec(x) % 100 === 0) ? 1 : 0; };
                    var isvalidunique = function (x) { return (x >= 15 && x <= 18) ? 1 : 0; };
                    var quantization_factor = timestamps.map(isquantized).mean();
                    var uniqueness_factor = timestamps.diff().getUnique().map(isvalidunique).sum();

                    callback(timestamps.diff().mean(), timestamps.diff().variance(),
                        quantization_factor, uniqueness_factor);
                }, 100);
            }
            else
                window.requestAnimationFrame(measureScreenRefreshIntervals_inner);
        };

        window.requestAnimationFrame(measureScreenRefreshIntervals_inner);
    };

    dltk.runBenchmark = function runBenchmark(callback, optdct) {

        // Runs a suite of benchmarks and calls the "callback".
        // - optdct: a dictionary of options (optional)
        //     tres_dur: the number of function calls to estimate
        //       time interval of setTimeout(, 0).
        //     mips_reps: the number of function calls to estimate
        //       bogoMIPS.
        //     canvas_test_fps: the canvas on which the fps benchmark
        //       will be run.
        //     canvas_test_color: color to be used in fps benchmark
        var tres_dur = defined(optdct) ? optdct.tres_dur : undefined;
        var mips_reps = defined(optdct) ? optdct.mips_reps : undefined;
        var canvas_test_fps = defined(optdct) ? optdct.canvas_test_fps : undefined;
        var canvas_test_color = defined(optdct) ? optdct.canvas_test_color : undefined;

        var api_support = true;
        // test api support level
        if (!callable(window.requestAnimationFrame))
            api_support = false;
        if (!defined(performance) || !callable(performance.now))
            api_support = false;

        // benchmark result set
        var result = {
            api_support: api_support,
            js_tres: undefined,
            js_tres_variance: undefined,
            bogoMIPS: undefined,
            refresh_interval: undefined,
            refresh_interval_variance: undefined,
        };

        if (!api_support) {
            if (callable(callback)) {
                return callback(result);
            } else {
                return result;
            }
        }

        // schedule benchmarks to be run **sequentially**
        dltk.queueJob(function() {
            dltk.measureTimeResolution(function (js_tres, js_tres_variance) {
                result.js_tres = js_tres;
                result.js_tres_variance = js_tres_variance;
                dltk.runQueuedJobs();
            }, tres_dur);
        });
        dltk.queueJob(function() {
            dltk.measureBogoMIPS(function (mips) {
                result.bogoMIPS = mips;
                dltk.runQueuedJobs();
            }, mips_reps);
        });
        dltk.queueJob(function() {
            if (!defined(canvas_test_fps)) {
                dltk.runQueuedJobs();
                return;
            }
            dltk.measureScreenRefreshInterval(canvas_test_fps,
                function(refresh_interval, refresh_interval_variance, quantization_factor, uniqueness_factor) {
                    result.refresh_interval = refresh_interval;
                    result.refresh_interval_variance = refresh_interval_variance;
                    result.refresh_interval_quantization_factor = quantization_factor;
                    result.refresh_interval_uniqueness_factor = uniqueness_factor;
                    dltk.runQueuedJobs();
                }, canvas_test_color);
        });
        dltk.queueJob(function() {
            if (callable(callback)) {
                return callback(result);
            } else {
                return result;  // but this won't do any in reality
            }
        });
        dltk.runQueuedJobs();
    };


    /*************************************************************************
     * Graphics/experiment control functions                                 *
     *************************************************************************/
    dltk.getContextsFromCanvas = function getContextsFromCanvas(onscr_canvas_id) {
        // For double buffering
        // from: http://blog.bob.sh/2012/12/double-buffering-with-html-5-canvas.html
        var ctxMain = dltk.getOnScreenContextFromCanvas(onscr_canvas_id);
        var ctxOffscreen = dltk.getOffScreenContext(ctxMain.canvas.width, ctxMain.canvas.height);

        return {onscr: ctxMain, offscr: ctxOffscreen};
    };

    dltk.getOnScreenContextFromCanvas = function getOnScreenContextFromCanvas(onscr_canvas_id) {
        var mainCanvas = document.getElementById(onscr_canvas_id);
        return mainCanvas.getContext('2d');
    };

    dltk.getOffScreenContext = function getOffScreenContext(w, h) {
        var offscreenCanvas = document.createElement('canvas');
        if (typeof(w) == 'number') offscreenCanvas.width = parseInt(w, 10);
        if (typeof(h) == 'number') offscreenCanvas.height = parseInt(h, 10);
        return offscreenCanvas.getContext('2d');
    };

    dltk.drawToContext = function drawToContext(imgurl, ctx, callback) {
        // Draw "imgurl" onto the context "ctx".  "callback" will be called upon success completion.
        // (from: https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Canvas_tutorial/Using_images)
        //
        // - imgurl: URL of the image to draw.  Also, the following special keys are supported:
        //      - "color:<name of the color to fill>" : Fill with the specified color
        var img;
        var t_draw_begin = performance.now();
        var w = ctx.canvas.width, h = ctx.canvas.height;

        if (imgurl.startsWith('color:')) {
            var color = imgurl.substring(6).trim();
            ctx.rect(0, 0, w, h);
            ctx.fillStyle = color;
            ctx.fill();

            if (callable(callback)) setTimeout(function() { callback(t_draw_begin); }, 0);
            // ^ use setTimeout to ensure callback() is called later than this function.
        }
        else {
            img =  new Image();
            img.onload = function() {
                ctx.drawImage(img, 0, 0, w, h);  // should stretch
                //ctx.drawImage(img, 0, 0);

                // if callback is requested...
                if (callable(callback)) callback(t_draw_begin);
            };
            img.src = imgurl;
        }
        return t_draw_begin;
    };

    dltk.copyContexts = function copyContexts(ctxsrc, ctxdst) {
        ctxdst.drawImage(ctxsrc.canvas, 0, 0);
    };

    dltk.prepareResourcesOnce = function prepareResourcesOnce(url, ctx_onscr, fn) {
        // Prepapre/preload the resource "url" that will be painted onto an on-screen
        // context "ctx_onscr" later.  This creates an off-screen context that matches
        // the size of the on-screen context "ctx_onscr", and draws the resource "url"
        // onto the off-screen context.
        // - fn: callback function that will be called upon successful preloading
        var w = ctx_onscr.canvas.width, h = ctx_onscr.canvas.height;
        var ctx_offscr;
        if (!(url in dltk.preloaded_rsrcs)) dltk.preloaded_rsrcs[url] = {};
        if (!([w, h] in dltk.preloaded_rsrcs[url])) {
            ctx_offscr = dltk.getOffScreenContext(w, h);
            dltk.drawToContext(url, ctx_offscr, fn);
            dltk.preloaded_rsrcs[url][[w, h]] = ctx_offscr;
        }
        else setTimeout(fn, 0);    // already processed. skip
    };

    dltk.prepareResources = function prepareResources(imgFiles, onScrContexts, callback, progressfn) {
        // Loads resources as specified by "imgFiles" and "responseContexts"
        // - imgFiles: should be the standard form of ExperimentData.imgFiles for n-AFC tasks
        //   where an element is a length-2 list of the following form:
        //      [test img url, [sample img 1 url, sample img 2 url, ..., sample img n url]]
        // - onScrContexts: a list that contains on-screen contexts where the stimuli will be
        //   painted onto.  The shape of this must match the that of an "imgFiles" element.

        var idx = 0;
        var idx_inner = 0;

        var prepareResources_inner = function prepareResources_inner() {
            if (idx >= imgFiles.length) {
                // -- done.
                if (callable(callback)) callback();
                return;
            }

            // -- not done
            // if all inner things for this idx is complete
            if (idx_inner >= imgFiles[idx][1].length + 1) {
                idx_inner = 0;
                idx++;
                if (callable(progressfn)) progressfn(idx, imgFiles.length);
                setTimeout(prepareResources_inner, 0);
                return;
            }
            // otherwise, run dltk.prepareResourcesOnce().
            // Next inner iteration will be scheduled inside dltk.prepareResourcesOnce().
            // process test stimulus:
            if (idx_inner === 0)
                dltk.prepareResourcesOnce(imgFiles[idx][0], onScrContexts[0], prepareResources_inner);
            // process response images:
            else
                dltk.prepareResourcesOnce(imgFiles[idx][1][idx_inner - 1], onScrContexts[1][idx_inner - 1],
                        prepareResources_inner);
            idx_inner++;
            // DO NOT SCHEDULE prepareResources_inner() HERE
        };
        setTimeout(prepareResources_inner, 0);
    };

    dltk.queueTrial = function queueTrial(specs, callback, optdct) {
        // queue and run one trial.
        // - specs: list of dictionaries of trial elements, where:
        //     specs[i].urls: list of URLs for the i-th component's image(s)
        //     specs[i].duration: duration of the i-th component
        //     specs[i].contexts: list of on-screen context(s) to where the image(s) will be drawn
        //     specs[i].pre: func to be called just before rendering i-th component (optional)
        //     specs[i].post: func to be called just after rendering i-th component (optional)
        // - callback: callback func to be called after the trial has ended (optional)
        // - optdct: dictionary of options (optional)
        //     measureFlushTiming: if true, measure the estimated time to get drawing
        //                         commands to get processed/flushed.
        var t0;
        var idx = -1;                 // current index of components
        var history = [], history_delta = [], history_delta_flush = [];
        var tstamps = [], tdeltas = [], tdeltaflushes = [];

        var optdct_measureFlushTiming = (defined(optdct) && defined(optdct.measureFlushTiming)) ? (optdct.measureFlushTiming === true) : false;

        var flush_duration = function flush_duration(te) {
            tdeltaflushes.push(performance.now() - te);
        };

        var render = function render(t) {
            var w, h, ctx, url, ctxs, urls, t_jitter, te;
            tstamps.push(t);

            // -- no need to update the screen
            if (idx >= 0) {
                // half-frame jitter is okay and probably unavoidable
                t_jitter = tstamps.slice(-(dltk.STATLEN_FPS + 1)).diff().mean() / 2;
                dltk._t_jitter = t_jitter;    // mainly for diagnostic/debug purposes

                if ((t - t0) < (specs[idx].duration - t_jitter)) {
                    // no drawing, done for now
                    te = performance.now();
                    tdeltas.push(te - t);
                    window.requestAnimationFrame(render);
                    if (optdct_measureFlushTiming)
                        setTimeout(function () { flush_duration(te); }, 0);
                    return;
                }
            }

            // -- update the screen
            idx++;
            history.push(tstamps);
            history_delta.push(tdeltas);
            history_delta_flush.push(tdeltaflushes);
            t0 = t;
            tstamps = [t0];
            tdeltas = [];
            tdeltaflushes = [];

            // finished?
            if (idx >= specs.length) {
                if (callable(callback)) callback(history, history_delta, history_delta_flush);
                return;
            }

            // do necessary setups prior to draw idx-th component
            if (callable(specs[idx].pre)) specs[idx].pre(history, history_delta, history_delta_flush);

            // render
            urls = specs[idx].urls;
            ctxs = specs[idx].contexts;   // on-screen contexts
            for (var j = 0; j < urls.length; j++) {
                url = urls[j];
                ctx = ctxs[j];
                w = ctx.canvas.width;
                h = ctx.canvas.height;
                // transfer preloaded image to ctx: should be fast
                dltk.copyContexts(dltk.preloaded_rsrcs[url][[w, h]], ctx);
            }

            // do necessary interventions after drawing of idx-th component
            if (callable(specs[idx].post)) specs[idx].post(history, history_delta, history_delta_flush);

            te = performance.now();
            tdeltas.push(te - t);
            window.requestAnimationFrame(render);
            if (optdct_measureFlushTiming)
                setTimeout(function () { flush_duration(te); }, 0);
        };
        window.requestAnimationFrame(render);
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
        for (var i = 0; i < this.length; i++) {
            if (!isFinite(this[i])) continue;
            sum += parseFloat(this[i]); ++j;
        }
        return j ? sum / j : 0;
    };

    window.Array.prototype.variance = function () {
        var sum = 0, j = 0, a;
        for (var i = 0; i < this.length; i++) {
            if (!isFinite(this[i])) continue;
            a = parseFloat(this[i]); ++j;
            sum += a * a;
        }
        a = this.mean();
        return j ? sum / j - a * a : 0;
    };

    window.Array.prototype.diff = function () {
        var res = [];
        for (var i = 0; i < this.length - 1; i++) {
            res.push(this[i + 1] - this[i]);
        }
        return res;
    };

    window.String.prototype.startsWith = function (str) {
        return this.indexOf(str) === 0;
    };

}(window.dltk = window.dltk || {}, window));
