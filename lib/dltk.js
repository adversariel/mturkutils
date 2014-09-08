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
    dltk.FRAME_INTERVAL_TOL = 1000 / 60 + 2;   // mean frame interval should be smaller than 16.66ms + 2ms
    dltk.FRAME_INTERVAL_VAR_TOL = 5 * 5;       // jitter shouldn't be larger than 5ms
    dltk.FRAME_INTERVAL_QUANTFAC_TOL = 0.8;    // fail if more than 80% of timestamps are multiples of 100us (FF)
    dltk.FRAME_INTERVAL_UNIQFAC_TOL = 3;       // fail if there are <= 3 unique intervals (Chrome)
    dltk.STATLEN_FPS = 2;             // use last two fps to figure out current fps

    dltk.preloaded_rsrcs = {};        // a dictionary of on/off screen contexts + etc. for preloaded imgs

    dltk.js_tres = null;              // setTimeout resolution...
    dltk.js_tres_variance = null;     // ...and variance
    dltk.bogoMIPS = null;             // same as the name
    dltk.refresh_test_timestamps = null;

    dltk._jobs = [];                  // functions to be called sequentially and asynchronously

    var document = window.document;
    var performance = window.performance;
    var navigator = window.navigator;
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

    var callable = function callable(obj) {
        return typeof(obj) == 'function';
    };
    dltk.callable = callable;  // also make public

    var defined = function defined(obj) {
        return typeof(obj) != 'undefined';
    };
    dltk.defined = defined;   // also make public

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

    dltk.detectMobile = function detectMobile() { 
        // from: http://stackoverflow.com/questions/11381673/javascript-solution-to-detect-mobile-browser
        if (navigator.userAgent.match(/Android/i) || navigator.userAgent.match(/webOS/i) ||
                navigator.userAgent.match(/iPhone/i) || navigator.userAgent.match(/iPad/i) ||
                navigator.userAgent.match(/iPod/i) || navigator.userAgent.match(/BlackBerry/i) ||
                navigator.userAgent.match(/Windows Phone/i))
            return true;
        return false;
    };

    var applyDefaults = function applyDefaults(paramdct, defaultdct) {
        if (!defined(paramdct)) return defaultdct;
        for (var k in defaultdct) {
            if (!defined(paramdct[k])) paramdct[k] = defaultdct[k];
        } 
        return paramdct;
    };
    dltk.applyDefaults = applyDefaults;

    dltk.roundNDecimal = function roundNDecimal(num, n) {
        n = parseInt(n, 10);
        var m = Math.pow(10, n);
        return Math.round(num * m) / m;
    };

    var round2 = function round2(num) {
        return dltk.roundNDecimal(num, 2);
    };
    dltk.round2 = round2;      // also make public

    var nop = function () { };   // function that does nothing

    dltk.BrowserDetect = {
        // Browser detection stuffs
        // references:
        //    http://stackoverflow.com/questions/588940/what-is-the-best-way-to-do-browser-detection-in-javascript
        //    http://www.quirksmode.org/js/detect.html
        // roughly same as: https://s3.amazonaws.com/dlcommon/js/browserdetect-0.0.1.js
        init: function (optStrictMode) {
            // by default, use strict mode
            var strict = defined(optStrictMode) ? optStrictMode : true;

            this.browser = this.searchString(this.dataBrowser, strict) || "An unknown browser";
            this.version = this.searchVersion(navigator.userAgent) ||
                this.searchVersion(navigator.appVersion) || "an unknown version";
            this.OS = this.searchString(this.dataOS, strict) || "an unknown OS";
        },
        searchString: function (data, strict) {
            for (var i = 0; i < data.length; i++) {
                // If not "strict", don't use strict-mode data
                if (!strict && data[i].strict === true) continue;
                var dataString = data[i].string;
                var dataProp = data[i].prop;
                this.versionSearchString = data[i].versionSearch || data[i].identity;
                if (dataString) {
                    if (dataString.indexOf(data[i].subString) != -1)
                        return data[i].identity;
                }
                else if (dataProp)
                    return data[i].identity;
            }
        },
        searchVersion: function (dataString) {
            var index = dataString.indexOf(this.versionSearchString);
            if (index == -1) return;
            return parseFloat(dataString.substring(index+this.versionSearchString.length+1));
        },
        dataBrowser: [
            {
                string: navigator.userAgent,
                subString: "Chrome",
                identity: "Chrome"
            },
            { 	string: navigator.userAgent,
                subString: "OmniWeb",
                versionSearch: "OmniWeb/",
                identity: "OmniWeb"
            },
            {
                string: navigator.vendor,
                subString: "Apple",
                identity: "Safari",
                versionSearch: "Version"
            },
            {
                prop: window.opera,
                identity: "Opera"
            },
            {
                string: navigator.vendor,
                subString: "iCab",
                identity: "iCab"
            },
            {
                string: navigator.vendor,
                subString: "KDE",
                identity: "Konqueror"
            },
            {   // for IE11+, otherwise reported as Mozilla
                string: navigator.userAgent,
                subString: "Trident/",
                identity: "Explorer",
                versionSearch: "rv",
                strict: true,
            },
            {
                string: navigator.userAgent,
                subString: "Firefox",
                identity: "Firefox"
            },
            {
                string: navigator.vendor,
                subString: "Camino",
                identity: "Camino"
            },
            {		// for newer Netscapes (6+)
                string: navigator.userAgent,
                subString: "Netscape",
                identity: "Netscape"
            },
            {
                string: navigator.userAgent,
                subString: "MSIE",
                identity: "Explorer",
                versionSearch: "MSIE"
            },
            {
                string: navigator.userAgent,
                subString: "Gecko",
                identity: "Mozilla",
                versionSearch: "rv"
            },
            { 		// for older Netscapes (4-)
                string: navigator.userAgent,
                subString: "Mozilla",
                identity: "Netscape",
                versionSearch: "Mozilla"
            }
        ],
        dataOS : [
            {
                string: navigator.platform,
                subString: "Win",
                identity: "Windows"
            },
            {
                string: navigator.platform,
                subString: "Mac",
                identity: "Mac"
            },
            {
                   string: navigator.userAgent,
                   subString: "iPhone",
                   identity: "iPhone/iPod"
            },
            {
                string: navigator.platform,
                subString: "Linux",
                identity: "Linux"
            }
        ]
    };
    dltk.BrowserDetect.init();                  // use the new "strict" mode, which detects IE11+ correctly
    window.BrowserDetect = dltk.BrowserDetect;  // <- DO NOT REMOVE: for compatibility 

    // Window dimensions and screen resolution stuffs
    dltk.getScreenAndWindowDimensions = function getScreenAndWindowDimensions(suppressGlobalVar) {
        var vertical, horizontal;   // <- hh: bad naming convention... but keeping for compatibility
        var winW, winH;

        vertical = window.screen.height;
        horizontal = window.screen.width;

        if (typeof(window.innerWidth) == 'number') {
            // Standard, Non-IE
            winW = window.innerWidth;
            winH = window.innerHeight;
        }
        else if (document.documentElement && 
                (document.documentElement.clientWidth || document.documentElement.clientHeight)) {
            // IE 6+ in 'standards compliant mode'
            winW = document.documentElement.clientWidth;
            winH = document.documentElement.clientHeight;
        }
        else if (document.body && (document.body.clientWidth || document.body.clientHeight)) {
            // IE 4 compatible
            winW = document.body.clientWidth;
            winH = document.body.clientHeight;
        }

        if (suppressGlobalVar !== true) {
            window.vertical = vertical;
            window.horizontal = horizontal;
            window.winW = winW;
            window.winH = winH;
        }

        return {winW: winW, winH: winH, horizontal: horizontal, vertical: vertical};
    };
    // the following causes setting of the following global vars: vertical, horizontal, var winW, winH
    // which are needed for backward compatibility
    dltk.getScreenAndWindowDimensions();  


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

    dltk.prepareResourcesOnce = function prepareResourcesOnce(url, ctx_onscr, fn, optdct) {
        // Prepapre/preload the resource "url" that will be painted onto an on-screen
        // context "ctx_onscr" later.  This creates an off-screen context that matches
        // the size of the on-screen context "ctx_onscr", and draws the resource "url"
        // onto the off-screen context.
        // - fn: callback function that will be called upon successful preloading
        // - optdct: a dictionary that specficies other options
        //    - rsrcs: specifies the dictionary that preloaded images will be saved to
        var w = ctx_onscr.canvas.width, h = ctx_onscr.canvas.height;
        var ctx_offscr;
        var optdct_default = {rsrcs: dltk.preloaded_rsrcs};
        optdct = dltk.applyDefaults(optdct, optdct_default);
        var rsrcs = optdct.rsrcs;

        if (!(url in rsrcs)) rsrcs[url] = {};
        if (!([w, h] in rsrcs[url])) {
            ctx_offscr = dltk.getOffScreenContext(w, h);
            dltk.drawToContext(url, ctx_offscr, fn);
            rsrcs[url][[w, h]] = ctx_offscr;
        }
        else setTimeout(fn, 0);    // already processed. skip
    };

    dltk.prepareResources = function prepareResources(imgFiles, onScrContexts, callback, progressfn, optdct) {
        // Loads resources as specified by "imgFiles" and "onScrContexts".
        // - imgFiles: should be the standard form of ExperimentData.imgFiles for n-AFC tasks
        //   where an element is a length-2 list of the following form:
        //      [test img url, [sample img 1 url, sample img 2 url, ..., sample img n url]]
        // - onScrContexts: a list that contains on-screen contexts where the stimuli will be
        //   painted onto.  The shape of this must match the that of an "imgFiles" element.
        //
        // Other optional parameters:
        // - callback: a function to be called upon successful preloading
        // - progressfn: a function to be called to show progress
        // - optdct: a dictionary that specficies other options
        //    - rsrcs: specifies the dictionary that preloaded images will be saved to
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
                dltk.prepareResourcesOnce(imgFiles[idx][0], onScrContexts[0], prepareResources_inner, optdct);
            // process response images:
            else
                dltk.prepareResourcesOnce(imgFiles[idx][1][idx_inner - 1], onScrContexts[1][idx_inner - 1],
                        prepareResources_inner, optdct);
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
        //     rsrcs: specifies the dictionary that contains preloaded images
        var t0;
        var idx = -1;                 // current index of components
        var history = [], history_delta = [], history_delta_flush = [];
        var tstamps = [], tdeltas = [], tdeltaflushes = [];

        var optdct_default = {rsrcs: dltk.preloaded_rsrcs, measureFlushTiming: false};
        optdct = dltk.applyDefaults(optdct, optdct_default);
        var rsrcs = optdct.rsrcs;
        var measureFlushTiming = optdct.measureFlushTiming;

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
                    if (measureFlushTiming)
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
                dltk.copyContexts(rsrcs[url][[w, h]], ctx);
            }

            // do necessary interventions after drawing of idx-th component
            if (callable(specs[idx].post)) specs[idx].post(history, history_delta, history_delta_flush);

            te = performance.now();
            tdeltas.push(te - t);
            window.requestAnimationFrame(render);
            if (measureFlushTiming)
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

    window.Array.prototype.sum = function() {
        // copied from zen library
        var i = this.length;
        var s = 0;
        while (i--) {
            s += this[i];
        }
        return s;
    };

    window.String.prototype.startsWith = function (str) {
        return this.indexOf(str) === 0;
    };

    
    /*************************************************************************
     * Classes that support various experiments
     *************************************************************************/

    // -- Main class that does various initialization and management stuffs
    dltk.Experiment = function Experiment(_$, optdct) {
        // -- Default constants
        var MSG_NO_MOBILE = "<span><font color=red style=background-color:white><b>" + 
            "Mobile devices are not supported.<br />Thank you!</b></font></span>";
        var MSG_NOT_SUPPORTED_OS = "<span><font color=red style=background-color:white><b>" + 
            "Only ${SUPPORTED_OS} are supported.<br />Thank you!</b></font></span>";
        var MSG_NOT_SUPPORTED_BROWSER = "<span><font color=red style=background-color:white><b>" + 
            "Please only use the latest version of ${SUPPORTED_BROWSER} for this HIT.<br />" + 
            "Thank you!</b></font></span>";
        var MSG_SCREEN_TOO_SMALL = "<span><font color=red style=background-color:white><b>" +
            "Screen smaller than ${MINSZ} is not supported.<br />Please try again with higher resolution. " + 
            "Thank you!</b></font></span>";
        var MSG_PREVIEW = "<font color=red style=background-color:white><b>You are in PREVIEW mode.<br />" + 
            "Please ACCEPT this HIT to complete the task and receive payment.</b></font>";
        var MSG_API_NOT_SUPPORTED = "Your browser seems to be outdated to run this task.  " + 
            "Please try with the newest ${SUPPORTED_BROWSER} please.";
        var MSG_JS_TRES_SLOW = "Your system is too slow to complete this task (t=${DIAG}).  " +
            "Close other programs/tabs please.";
        var MSG_JS_TRES_HIGH_VARIANCE = "Your system's clock varies too much (v=${DIAG}).  " + 
            "Close other programs/tabs please.";
        var MSG_FF_BADSTATE = "Your browser's timestamps are too inaccurate (q=${DIAG}).  " +
            "Please first make sure you're using the latest version of Firefox.  " +
            "If this browser has been running for a long time or the computer was suspended while " +
            "running this browser, you need to restart the browser (not just closing and re-opening " +
            "this tab only) to run this task.";
        var MSG_CR_BADSTATE_FF_SUPPORTED = "Your browser's timestamps are too inaccurate (u=${DIAG}).  " +
            "Please first make sure you're using the latest version of Chrome.  If this browser has been " +
            "running for a long time or the computer was suspended while running this browser, " +
            "restarting the browser (not just closing and re-opening this tab only) will solve this " +
            "problem most of the time.  However, if that doesn't work, one of the following options " +
            "should fix the problem: (1) Use the latest version of Firefox; or (2) Restart your computer.";
        var MSG_CR_BADSTATE_NO_FF = "Your browser's timestamps are too inaccurate (u=${DIAG}).  " +
            "Please first make sure you're using the latest version of Chrome.  If this browser has been " +
            "running for a long time or the computer was suspended while running this browser, " +
            "restarting the browser (not just closing and re-opening this tab only) will solve this " +
            "problem most of the time.  However, if that trick doesn't work, you need to restart your computer.";
        var MSG_SUFF_BADSTACE = " If you believe this error was just a hiccup, you can try this browser " +
            "testing again. Do you want to retry?";
        var MSG_SLOW_FPS = "Your browser's refresh rate is slower than 60fps (f=${DIAG}).  " +
            "Close other programs/tabs please.";
        var MSG_HIGH_FPS_VARIANCE = "Your browser's refresh rate varies too much (v=${DIAG}).  " +
            "Close other programs/tabs please.";
        var MSG_NOOK = "<font color=red style=background-color:white><b>Your system CANNOT run this HIT " +
            "at this point: ${REASON}</b></font>";
        var MSG_WAIT = "<font color=red style=background-color:white><b>Wait: your system is being tested " +
            "to check if it can run this task...</b></font>";
        // A default list of elements that will be recentered upon screen resize (if recomputeOffset is enabled)
        var RECOMPUTE_OFFSET_RECENTER = ['elemUpperRightGroup'];
        // These will be recentered after passing benchmark  (if recomputeOffset is enabled)
        var RECOMPUTE_OFFSET_RECENTER_AFTER_BENCHMARK = ['elemWarning', 'elemPreload']; 

        var OS = dltk.BrowserDetect.OS;
        var BROWSER = dltk.BrowserDetect.browser;

        var OPTDCT_DEFAULT = {
            /*** various document elements ***/
            elemFallback: null,         // things to display when everything fails
            elemSystemmsg: null,        // dialog box for benchmark failures and stuffs like that
            elemWarning: null, elemPreload: null,    // warning and preload text lines
            elemUpperRightGroup: null,  // this should contain elemTutorialLink and elemTimer
            elemTutorialLink: null, elemTimer: null,
            elemTutorial: null,         // this will be tutorial dialog box
            elemNotice: null,           // things to display when the task is ready to go, below the instructions
            elemBeginTaskGroup: null,   // this contains all stuffs that begin experiment (e.g. elemBeginTaskBtn)
            elemBeginTaskBtn: null,     // this will be the button that actually start the experiment 
            elemFPSBench: null,         // the element contains the fps benchmark canvas
            elemFPSBenchCanvasID: undefined,  // <- default must be undefined.  DONT PREPEND "#"!!
            /*** various hook functions ***/
            onAfterPassBenchmark: null,
            onAfterPreloadAllModulesRsrcs: null,
            onBeginExp: null,
            onRecomputeOffset: null,
            onRunNextTrial: null,
            /*** experiment flow control flags ***/
            automaticallyRunPreloadAfterPassBenchmark: true,
            automaticallyRunPreBeginExpAfterPreload: true,
            automaticallyRunNextTrialOnBeginExp: true,   // run the 1st trial automatically when Begin btn clicked?
            /*** allowed systems ***/
            allowMobile: false,
            supportedOS: ['Windows', 'Mac', 'Linux'],  // pass null if you want to disable this check
            supportedBrowser: ['Chrome', 'Firefox'],   // pass null to disable. also don't add browsers without performance.now()
            minVertical: 600, minHorizontal: 1000,
            /*** dialogbox settings ***/
            systemMsgDialogPosition: ['middle', 30],   
            tutorialContents: '',
            tutorialDialogHeight: 560,
            tutorialDialogWidth: 900,
            tutorialDialogPosition: 'center',
            tutorialDialogTitle: "Instructions",
            /*** other settings ***/
            recomputeOffsetRecenterList: null,   // if null, RECOMPUTE_OFFSET_RECENTER is used
            recomputeOffsetRecenterAfterBenchmarkList: null,  // if null, RECOMPUTE_OFFSET_RECENTER_AFTER_BENCHMARK is used
            timerSloppyness: 5,
            FPSBenchColor: undefined,  // default must be undefined
            maxHeightInThisExp: 500,   // the # of pixels needed for this experiment.  Used in recomputeOffset()
            expLoadTime: new Date(),
            assignmentIDURLParameter: 'assignmentId',
            useAlert: false,
            useRecomputeOffset: false,
            printDbgMessage: false,
            /*** set some of beloew to override displayed messages ***/
            msgNoMobile: MSG_NO_MOBILE,
            msgNotSupportedOS: MSG_NOT_SUPPORTED_OS,
            msgNotSupportedBrowser: MSG_NOT_SUPPORTED_BROWSER,
            msgScreenTooSmall: MSG_SCREEN_TOO_SMALL,
            msgPreview: MSG_PREVIEW,
            msgAPINotSupported: MSG_API_NOT_SUPPORTED,
            msgJSTResSlow: MSG_JS_TRES_SLOW,
            msgJSTResHighVariance: MSG_JS_TRES_HIGH_VARIANCE,
            msgSuffBadState: MSG_SUFF_BADSTACE,
            msgFFBadState: MSG_FF_BADSTATE,
            msgCRBadStateFFSupported: MSG_CR_BADSTATE_FF_SUPPORTED,
            msgCRBadStateNoFF: MSG_CR_BADSTATE_NO_FF,
            msgSlowFPS: MSG_SLOW_FPS,
            msgHighFPSVariance: MSG_HIGH_FPS_VARIANCE,
            msgNOOK: MSG_NOOK,
            msgWait: MSG_WAIT,
            /*** benchmark thresholds - do not change unless you know what you're doing ***/
            JS_TRES_TOL: dltk.JS_TRES_TOL,
            JS_TRES_VAR_TOL: dltk.JS_TRES_VAR_TOL,
            FRAME_INTERVAL_QUANTFAC_TOL: dltk.FRAME_INTERVAL_QUANTFAC_TOL,
            FRAME_INTERVAL_UNIQFAC_TOL: dltk.FRAME_INTERVAL_UNIQFAC_TOL,
            FRAME_INTERVAL_TOL: dltk.FRAME_INTERVAL_TOL,
            FRAME_INTERVAL_VAR_TOL: dltk.FRAME_INTERVAL_VAR_TOL,
        };

        // -- Private variables
        var that = this;   // this is needed for inner functons to access "this"
        var o = dltk.applyDefaults(optdct, OPTDCT_DEFAULT);   // shorthand for optdct
        var $ = function $(elem) {
            // safety wrapper to jquery: if no jquery is provided or the elemnt is missing
            // returns a wrapper that does nothing
            var target = defined(_$) ? _$(elem) : null;
            if (target === null || target.length === 0) {
                that.setDebugMessage('$: NOOP: ' + elem);
                return {hide: nop, show: nop, click: nop, html: nop, append: nop,
                    dialog: nop, css: nop, bind: nop};
            }
            return target;
        };

        // -- Public variables
        this.exp_started = false;   // is experiment started?
        this.aID = dltk.getURLParameter(o.assignmentIDURLParameter);  // assignmentID
        this.benchmark_passed = false;
        this.benchmark_finished = false;
        this.benchmark = null;   // last benchmark
        this.benchmarks = [];    // all benchmark results
        this._timer_bench = null;
        this._timer_disp = null;
        this._debugMsg = '';
        this.modules = [];   // list of modules. Public, but ALMOST ALL THE CASES shouldn't be accessed directly
        // modules_isenabled: boolean list, where each elem determines if the module is enabled or not.
        // Enabled modules' hook functions will be called when necessary, whease disabled modules' not.
        this.modules_isenabled = [];
        // module_active: a index number that points to the current active module.  There is only one active module.
        // This is different from enable/disabled modules in that "module_active" is mainly used as a shortcut
        // to call getXXX() methods without actually specifying the module index.  See callModule() for details.
        this.module_active = null;

        // -- Experimental methods that are private.  DO NOT CALL THESE DIRECTLY
        var _callHookfunctions = function _callHookfunctions(name, argdct) {
            // call all hook functions in enabled modules and optdct
            for (var i = 0; i < that.modules.length; i++)
                if (that.modules_isenabled[i] && callable(that.modules[i][name]))
                    that.modules[i][name](argdct);
            if (callable(o[name])) o[name](argdct);
        };

        var _preloadNextModuleRsrcs = function _preloadNextModuleRsrcs(idx) {
            // Call each module's preloaing routines one by one asynchronously.
            var i = defined(idx) ? idx : 0;
            if (i < 0 || i >= that.modules.length) {
                // finished preloading
                _callHookfunctions('onAfterPreloadAllModulesRsrcs');
                if (o.automaticallyRunPreBeginExpAfterPreload) that.preBeginExp();
                return;
            }
            if (!callable(that.modules[i].onPreloadRsrcsAsync)) {
                _preloadNextModuleRsrcs(i + 1);
                return;
            }

            var argdct = {
                finished: function () { _preloadNextModuleRsrcs(i + 1); },
            };
            that.modules[i].onPreloadRsrcsAsync(argdct);
            // ^ the module's onPreloadRsrcsAsync() MUST call argdct.finished() upon successful
            // finish of preloading resources.  Otherwise, the experiment will hang.
        };

        var _afterPassBenchmark = function _afterPassBenchmark() {
            // called after the benchmark passed
            that.benchmark_passed = true;

            if (o.useRecomputeOffset) that.recomputeOffset();
            if (that.aID == "ASSIGNMENT_ID_NOT_AVAILABLE") {
                $(o.elemWarning).show();
                $(o.elemWarning).html(o.msgPreview);
            }
            $(o.elemUpperRightGroup).show();
            $(o.elemTutorialLink).show();
            $(o.elemTimer).show();
            $(o.elemFPSBench).hide();
            $(o.elemNotice).show();

            $(o.elemTutorialLink).click(that.showTutorial);  // make it clickable to show tutorial
            that.startClock();
            that.showTutorial();

            _callHookfunctions('onAfterPassBenchmark');

            if (o.automaticallyRunPreloadAfterPassBenchmark) _preloadNextModuleRsrcs(0);
        };

        var _checkSystem = function _checkSystem(benchmark) {
            // determine if this system is capable of running this task
            // based on the benchmark result
            var nook = false;
            var failed_permanently = false;
            var details, suff = " Do you want to retry?";
            var msg_height = 260, msg_width = 460;
            var msg, pos;

            if (that.benchmark_finished) return;

            that.benchmark_finished = true;
            that.benchmark = benchmark;
            that.benchmarks.push(that.benchmark);
            if (that._timer_bench !== null) {
                clearTimeout(that._timer_bench);
                that._timer_bench = null;
            }

            if (!benchmark.api_support) {
                msg = o.supportedBrowser.join(', ');
                pos = msg.lastIndexOf(', ');
                msg = (pos < 0) ? msg : msg.slice(0, pos) + ' or' + msg.slice(pos + 1);

                details = o.msgAPINotSupported.replace('${SUPPORTED_BROWSER}', msg);
                nook = true;
                failed_permanently = true;
            }
            else if (benchmark.js_tres > o.JS_TRES_TOL) {
                details = o.msgJSTResSlow.replace('${DIAG}', String(round2(benchmark.js_tres)));
                nook = true;
            }
            else if (benchmark.js_tres_variance > o.JS_TRES_VAR_TOL) {
                details = o.msgJSTResHighVariance.replace('${DIAG}', String(round2(benchmark.js_tres_variance)));
                nook = true;
            }
            else if (BROWSER == 'Firefox' &&
                    benchmark.refresh_interval_quantization_factor > o.FRAME_INTERVAL_QUANTFAC_TOL) {
                details = o.msgFFBadState.replace('${DIAG}',
                        String(round2(benchmark.refresh_interval_quantization_factor)));
                suff = o.msgSuffBadState;
                nook = true;
                msg_height = 350;
                msg_width = 700;
            }
            else if (BROWSER == 'Chrome' &&
                    benchmark.refresh_interval_uniqueness_factor <= o.FRAME_INTERVAL_UNIQFAC_TOL) {
                if (o.supportedBrowser.indexOf('Firefox') < 0) details = o.msgCRBadStateNoFF;
                else details = o.msgCRBadStateFFSupported;
                details = details.replace('${DIAG}',
                        String(round2(benchmark.refresh_interval_uniqueness_factor)));
                suff = o.msgSuffBadState;
                nook = true;
                msg_height = 350;
                msg_width = 700;
            }
            else if (benchmark.refresh_interval > o.FRAME_INTERVAL_TOL) {
                details = o.msgSlowFPS.replace('${DIAG}',
                        String(round2(1000 / benchmark.refresh_interval)));
                nook = true;
            }
            else if (benchmark.refresh_interval_variance > o.FRAME_INTERVAL_VAR_TOL) {
                details = o.msgHighFPSVariance.replace('${DIAG}',
                        String(round2(benchmark.refresh_interval_variance)));
                nook = true;
            }

            // if something's wrong, display message and quit
            if (nook) {
                $(o.elemPreload).hide();
                $(o.elemWarning).show();
                $(o.elemWarning).html(o.msgNOOK.replace('${REASON}', details));
                if (failed_permanently) {
                    if (o.useAlert) alert(details);
                }
                else {
                    $(o.elemSystemmsg).show();
                    $(o.elemSystemmsg).html(details + suff);
                    $(o.elemSystemmsg).dialog({
                        height: msg_height,
                        width: msg_width,
                        modal: true,
                        position: o.systemMsgDialogPosition,
                        title: "Warning",
                        buttons: {
                            "Retry": function() {
                                $(this).dialog("close");
                                that.benchmark_finished = false;
                                that.testSystemAndPrepExp();
                            },
                            Cancel: function() {
                                $(this).dialog("close");
                            }
                        }
                    });
                }
            }
            // passed! proceed to experiment preps.
            else _afterPassBenchmark();
        };

        // -- Experimental methods that are public
        this.setDebugMessage = function setDebugMessage(msg) {
            that._debugMsg = msg;
            if (o.printDbgMessage) window.console.log(msg);
        };

        this.getDebugMessage = function getDebugMessage() {
            return that._debugMsg;
        };

        this.beginExp = function beginExp() {
            // This begins the experiment.
            // Called e.g. when Begin! button is clicked
            that.exp_started = true;
            $(o.elemBeginTaskBtn).hide();
            $(o.elemBeginTaskGroup).hide();
            $(o.elemPreload).hide();
            $(o.elemNotice).hide();
            _callHookfunctions('onBeginExp');

            // All preps are done.  Run the first trial 
            if (o.automaticallyRunNextTrialOnBeginExp) that.runNextTrial();
        };

        this.showTutorial = function showTutorial() {
            // show tutorial dialog box
            $(o.elemTutorial).show();
            $(o.elemTutorial).html(o.tutorialContents);
            $(o.elemTutorial).dialog({
                height: o.tutorialDialogHeight,
                width: o.tutorialDialogWidth,
                modal: true,
                position: o.tutorialDialogPosition,
                title: o.tutorialDialogTitle
            });
        };

        this.testSystemAndPrepExp = function testSystemAndPrepExp() {
            // Test the system, get benchmark results, and preps experiment variables
            $(o.elemWarning).hide();
            $(o.elemPreload).show();
            $(o.elemPreload).html(o.msgWait);
            $(o.elemFPSBench).show();

            dltk.runBenchmark(_checkSystem, {canvas_test_fps: o.elemFPSBenchCanvasID,
                canvas_test_color: o.FPSBenchColor});   // run benchmark...
            that._timer_bench = setTimeout(function() {           // ... or fall back to failure mode in 1 min.
                _checkSystem({api_support: false}); 
                }, 60 * 1000);
        };

        this.stopClock = function stopClock() {
            // Pause the timer display
            if (that._timer_disp === null) return;
            clearInterval(that._timer_disp);
            that._timer_disp = null;
        };

        this.startClock = function startClock() {
            // Start the timer display
            var updateTimer = function updateTimer () {
                var slop = o.timerSloppyness;
                var elapsed = parseInt((new Date() - o.expLoadTime) / 1000, 10) + slop;
                var minutes = parseInt(elapsed / 60, 10);
                var seconds = elapsed % 60;
                var minutes_str = (minutes <= 9) ? '0' : '';
                var seconds_str = (seconds <= 9) ? '0' : '';
                minutes_str += minutes;
                seconds_str += seconds;

                $(o.elemTimer).html('Time Passed: ' + minutes_str + ':' + seconds_str);
            };

            that._timer_disp = setInterval(updateTimer, 1000);
            updateTimer();  // update once NOW.
        };

        this.recomputeOffset = function recomputeOffset() {
            // Recenters few stuffs by using heuristics.  (Feel free to contribute if you have better ones.)
            // This is mainly used to circumvent bad rendetion of position:fixed inside iframe
            var diminfo = dltk.getScreenAndWindowDimensions(true);   // this doesn't update global variables
            var winW = diminfo.winW;
            var winH = diminfo.winH;
            var vertical = diminfo.vertical;
            var horizontal = diminfo.horizontal;
            var i, elem;

            // kludge...
            var thickness = window.outerHeight - winH;
            if (thickness < 10) thickness = 100;
            else if (thickness > 250) thickness = 250;
            thickness += 80;

            var offsetToTop = -parseInt(Math.min(
                        Math.max((vertical - thickness) / 2, o.maxHeightInThisExp / 2),
                        winH / 2), 10);

            if (that.benchmark_passed) {
                for (i = 0; i < o.recomputeOffsetRecenterAfterBenchmarkList.length; i++) {
                    elem = o.recomputeOffsetRecenterAfterBenchmarkList[i];
                    $(elem).css('position', 'absolute');
                    $(elem).css('top', '50%');
                    $(elem).css('margin-top', offsetToTop + 'px');
                }
            }
            for (i = 0; i < o.recomputeOffsetRecenterList.length; i++) {
                elem = o.recomputeOffsetRecenterList[i];
                $(elem).css('margin-top', offsetToTop + 'px');
            }

            _callHookfunctions('onRecomputeOffset', {winW: winW, winH: winH,
                horizontal: horizontal, vertical: vertical,    // <- bad naming convention...
                offsetToTop: offsetToTop});
            that.setDebugMessage('recomputeOffset: Resized event detected:' + offsetToTop);
        };

        this.preBeginExp = function preBeginExp() {
            // Show Begin button and make it clickable
            //$('#_preload').html("<font color=red style=background-color:white><b>Ready</b></font>");
            $(o.elemPreload).hide();
            $(o.elemBeginTaskBtn).show();
            $(o.elemBeginTaskGroup).show();
        };

        this.init = function init() {
            // Preps variables and do *minimal* compatibility checks
            var vertical = window.screen.height;
            var horizontal = window.screen.width;
            var msg, pos, i;

            // initial layout: hide all
            $(o.elemFallback).hide();
            $(o.elemTutorial).hide();
            $(o.elemSystemmsg).hide();
            $(o.elemNotice).hide();
            $(o.elemUpperRightGroup).hide();
            $(o.elemTutorialLink).hide();
            $(o.elemTimer).hide();
            $(o.elemPreload).hide();
            // begintask button is enabled, but hidden at start
            $(o.elemBeginTaskBtn).click(that.beginExp);
            $(o.elemBeginTaskBtn).hide();
            $(o.elemBeginTaskGroup).hide();
            $(o.elemWarning).hide();
            $(o.elemFPSBench).hide();
            // DO NOT HIDE "elemFPSBenchCanvasID"

            // reject unsupported devices
            if (!o.allowMobile && dltk.detectMobile()) {
                $(o.elemWarning).show();
                $(o.elemWarning).append(o.msgNoMobile);
                that.setDebugMessage(o.msgNoMobile);
                return false;
            }
            if (o.supportedOS !== null && o.supportedOS.indexOf(OS) < 0) {
                msg = o.supportedOS.join(', ');
                pos = msg.lastIndexOf(', ');
                msg = (pos < 0) ? msg : msg.slice(0, pos) + ' and' + msg.slice(pos + 1);
                msg = o.msgNotSupportedOS.replace('${SUPPORTED_OS}', msg);

                $(o.elemWarning).show();
                $(o.elemWarning).append(msg);
                that.setDebugMessage(msg);
                return false;
            }
            if (o.supportedBrowser !== null && 
                    (o.supportedBrowser.indexOf(BROWSER) < 0 || !defined(vertical) || !defined(horizontal))) {
                msg = o.supportedBrowser.join(', ');
                pos = msg.lastIndexOf(', ');
                msg = (pos < 0) ? msg : msg.slice(0, pos) + ' or' + msg.slice(pos + 1);
                msg = o.msgNotSupportedBrowser.replace('${SUPPORTED_BROWSER}', msg);

                $(o.elemWarning).show();
                $(o.elemWarning).append(msg);
                that.setDebugMessage(msg);
                return false;
            }
            if (vertical < o.minVertical || horizontal < o.minHorizontal) {
                msg = o.msgScreenTooSmall;
                msg = msg.replace('${MINSZ}', String(o.minHorizontal) + 'x' + String(o.minVertical));

                $(o.elemWarning).show();
                $(o.elemWarning).append(msg);
                that.setDebugMessage(msg);
                return false;
            }

            // -- now it's good to go
            if (o.recomputeOffsetRecenterList === null) {
                o.recomputeOffsetRecenterList = [];
                for (i = 0; i < RECOMPUTE_OFFSET_RECENTER.length; i++)
                    o.recomputeOffsetRecenterList.push(o[RECOMPUTE_OFFSET_RECENTER[i]]);
            }
            if (o.recomputeOffsetRecenterAfterBenchmarkList === null) {
                o.recomputeOffsetRecenterAfterBenchmarkList = [];
                for (i = 0; i < RECOMPUTE_OFFSET_RECENTER_AFTER_BENCHMARK.length; i++)
                    o.recomputeOffsetRecenterAfterBenchmarkList.push(o[RECOMPUTE_OFFSET_RECENTER_AFTER_BENCHMARK[i]]);
            }
            if (o.useRecomputeOffset) {
                window.onresize = that.recomputeOffset;
                that.recomputeOffset();
            }

            return true;  // successful init
        };

        this.isStarted = function isStarted() {
            return that.exp_started;
        };

        this.runNextTrial = function runNextTrial() {
            // Proceed to the next trial
            if (!that.exp_started) return;
            _callHookfunctions('onRunNextTrial');
        };

        this.getBenchmarkResults = function getBenchmarkResults() {
            // Get all the benchmark results as a list (one element per each benchmark run)
            return that.benchmarks;
        };

        this.getAssignmentID = function getAssignmentID() {
            return that.aID;
        };

        this.addModule = function addModule(module, optdctmodule) {
            // Add an experimental module (e.g., RSVP module)
            var handle = that.modules.length;
            var m = new module($, optdctmodule, o, that);
            if (!callable(m.init) || !m.init()) return -1;
            
            that.modules.push(m);
            that.modules_isenabled.push(true);
            if (that.modules.length != that.modules_isenabled.length) {
                that.setDebugMessage('addModule: modules.length != modules_isenabled.length');
                return -1;
            }
            // success!
            that.module_active = handle;
            return handle;
        };

        this.disableModule = function disableModule(handle) {
            // Disable "handle"-th module from interacting with this Experiment object.
            if (handle < 0 || handle >= that.modules.length) return false;
            that.modules_isenabled[handle] = false;
            return true;
        };

        this.disableAllModules = function disableAllModules() {
            for (var i = 0; i < that.modules.length; i++)
                that.disableModule(i);
        };

        this.enableModule = function enableModule(handle) {
            // Enable"handle"-th module from interacting with this Experiment object.
            if (handle < 0 || handle >= that.modules.length) return false;
            that.modules_isenabled[handle] = true;
            return true;
        };

        this.enableAllModules = function enableAllModules() {
            for (var i = 0; i < that.modules.length; i++)
                that.enableModule(i);
        };

        this.setActiveModule = function setActiveModule(handle) {
            if (handle < 0 || handle >= that.modules.length) return false;
            that.module_active = handle;
            return true;
        };

        this.callModule = function callModule(arg1, arg2, arg3) {
            // Call a module's method
            // Examples:
            // This calls "module_handle"-th module's theMethodToCall()
            //    callModule(module_handle, 'theMethodToCall')  
            // This calls "module_handle"-th module's theMethodToCall() with an argument "arg"  
            //    callModule(module_handle, 'theMethodToCall', arg)
            // This calls the current active module's theMethodToCall()
            //    callModule('theMethodToCall')
            //  Same, but passing an argument "arg" to the function
            //    callModule('theMethodToCall', arg)
            var fn, arg, module_handle;
            
            if (typeof(arg1) == 'string') {
                // module_handle is omitted
                module_handle = that.module_active;
                fn = arg1;
                arg = arg2;
            }
            else {
                module_handle = (!defined(arg1) || arg1 === null) ? that.module_active : arg1;
                fn = arg2;
                arg = arg3;
            }

            if (!callable(that.modules[module_handle][fn]))
                return null;
            return that.modules[module_handle][fn](arg);
        };

        this.callAllModules = function callAllModules(fn, arg) {
            // Call all modules' fn with an argument arg
            var nums = [];
            for (var i = 0; i < that.modules.length; i++) {
                nums.push(that.callModule(i, fn, arg));
            }
        };

        this.getCurrentTrialInfo = function getCurrentTrialInfo(module_handle) {
            // get the current trial info of the chosen module
            return that.callModule(module_handle, 'getCurrentTrialInfo');
        };

        this.getAllCurrentTrialInfo = function getAllCurrentTrialInfo() {
            // get the current trial info of all modules
            return that.callAllModules('getCurrentTrialInfo');
        };

        this.getCurrentTrialNumber = function getCurrentTrialNumber(module_handle) {
            // get the current trial # of the chosen module
            return that.callModule(module_handle, 'getCurrentTrialNumber');
        };

        this.getAllCurrentTrialNumbers = function getAllCurrentTrialNumbers() {
            // get the current trial numbers of all modules
            return that.callAllModules('getCurrentTrialNumber');
        };

        this.getTotalTrialNumber = function getTotalTrialNumber(module_handle) {
            // get the total trial # of the chosen module
            return that.callModule(module_handle, 'getTotalTrialNumber');
        };

        this.getAllTotalTrialNumbers = function getAllTotalTrialNumbers() {
            // get the total trial numbers of all modules
            return that.callAllModules('getTotalTrialNumber');
        };

        this.setCurrentTrialNumber = function setCurrentTrialNumber(num, module_handle) {
            // Sets the current trialNumber of "module_handle"-th module.
            if (module_handle < 0 || module_handle >= that.modules.length) {
                that.setDebugMessage('setCurrentTrialNumber: Invalid module_handle');
                return false;
            }
            if (!callable(that.modules[module_handle].setCurrentTrialNumber)) {
                that.setDebugMessage("setCurrentTrialNumber: the module dosen't support setCurrentTrialNumber");
                return false;
            }
            return that.modules[module_handle].setCurrentTrialNumber(num);
        };

        this._updateOptions = function _updateOptions(optdct) {
            // Provides an on-the-fly way to change some options
            // This is mainly provided for debugging/diagnosis purposes.
            // Be extra careful when use this; don't use unless you know what you're doing.
            if (!defined(optdct)) return;
            o = dltk.applyDefaults(optdct, o);
        };
    };  // end of Experiment
    

    // -- Experimental module that is used for RSVP style tasks
    dltk.RSVPModule = function RSVPModule($, optdctmodule, optdctexp, exp) {
        // A module that implements RSVP tasks.  This must be called by an Experiment object, not directly
        // by the user.  Parameters:
        // - $: the "sanitized" jquery object provided by the Experiment object
        // - optdctmodule: dictionary that contains options for this RSVP module
        // - optdctexp: dictionary that contains options that was used to instantiate the ``exp``
        // - exp: The Experiment object calling this module
        //
        // -- Default constants
        var MSG_TRIAL_PROGRESS = 'Progress:<br /> ${CURRENT} of ${TOTAL}';
        var IMG_FIXATION = 'https://s3.amazonaws.com/task_images/fixation_360x360.png';
        var IMG_BLANK = 'https://s3.amazonaws.com/task_images/blank_360x360.png';
        var default_onUpdatePreloadProgress = function (argdct) {
            var progress = argdct.progress, total = argdct.total;
            var msg = "<font color=red style=background-color:white><b>Processing resources: " + 
                progress + "/" + total + "</b></font>";
            argdct.msg = msg;
        };

        var OPTDCTMODULE_DEFAULT = {
            /******* basic setup vars **********/
            elemSample: null, elemTest: null,   // html elems that fully contain sample and test stuffs respectively
            elemSampleCanvasID: null,  // canvas id to which the RSVP stimuli will be painted on. do not prepend #
            elemTestCanvasIDs: null,   // canvas ids for ans choices. must match the shape of imgFiles[0]. no #
            elemTestClickables: null,  // elements that will be made clickable to receive answers
            elemTrialCounter: null,
            imgFiles: null,
            ISIs: null,                // list of ISIs for trials
            stimdurations: null,       // list of stimdurations for trials
            /******** hook functions: these MUST be short to run (ideally less than 2ms) ***********/
            onUpdatePreloadProgress: default_onUpdatePreloadProgress,
            onPreISI1: null,
            onPostISI1: null,
            onPreStim: null,
            onPostStim: null,
            onPreISI2: null,
            onPosISI2: null,
            onPreDrawResponse: null,
            onPostDrawResponse: null,
            onResponseReady: null,
            onClickedTestBtn: null,
            /******** text constants **********/
            msgTrialProgress: MSG_TRIAL_PROGRESS,
            imgFixation: IMG_FIXATION,
            imgBlank: IMG_BLANK,
        };

        // -- Private variables
        var o = optdctexp;   // short hand for Experiment object optdct
        var m = dltk.applyDefaults(optdctmodule, OPTDCTMODULE_DEFAULT);
        var that = this;
        var ctx_sample_on;
        var ctxs_test_on = [];
        var rsrcs = {};       // preloaded resources goes to here, not to the dltk.preloaded_rsrcs
        var primed = false;

        // -- Public variables
        this.totalTrials = null;
        this.trialNumber = null;

        // -- Private methods
        var _callHookfunctions = function _callHookfunctions(name, argdct) {
            if (callable(m[name])) m[name](argdct);
        };

        var _preISI1 = function _preISI1() {
            $(m.elemTest).hide();
            $(m.elemSample).show();
            // window.scrollTo(0, 0); // this causes suboptimal performance (forced sync)
            _callHookfunctions('onPreISI1');
        };
        var _postISI1 = function _postISI1() { _callHookfunctions('onPostISI1'); };
        var _preStim = function _preStim() { _callHookfunctions('onPreStim'); };
        var _postStim = function _postStim() { _callHookfunctions('onPostStim'); };
        var _preISI2 = function _preISI2() { _callHookfunctions('onPreISI2'); };
        var _postISI2 = function _postISI2() { _callHookfunctions('onPostISI2'); };
        var _preDrawResponse = function _preDrawResponse() {
            var msg = m.msgTrialProgress;
            msg = msg.replace('${CURRENT}', String(that.trialNumber + 1));
            msg = msg.replace('${TOTAL}', String(that.totalTrials));
            $(m.elemTrialCounter).html(msg);
            $(m.elemTest).show();
            $(m.elemSample).hide();
            _callHookfunctions('onPreDrawResponse');
        };
        var _postDrawResponse = function _postDrawResponse() { _callHookfunctions('onPostDrawResponse'); };

        var _runTrialOnce = function _runTrialOnce() {
            // Run single trial by using the new framework
            var trial_specs = [];
            var imgFiles = m.imgFiles;
            var trialNumber;

            if (that.trialNumber >= that.totalTrials) return;  // exceeded trials. abort.
            trialNumber = ++that.trialNumber;
            exp.stopClock();   // stop to minimize display burden

            // ISI 1 fixation dot
            trial_specs.push({
                urls: [m.imgFixation],
                contexts: [ctx_sample_on],
                duration: m.ISIs[trialNumber],
                pre: _preISI1,    // this MUST be short to run
                post: _postISI1   // this MUST be short to run
            });
            // sample stimulus
            trial_specs.push({
                urls: [imgFiles[trialNumber][0]],
                contexts: [ctx_sample_on],
                duration: m.stimdurations[trialNumber],
                pre: _preStim,    // this MUST be short to run
                post: _postStim   // this MUST be short to run
            });
            // ISI 2 blank
            trial_specs.push({
                urls: [m.imgBlank],
                contexts: [ctx_sample_on],
                duration: m.ISIs[trialNumber],
                pre: _preISI2,    // this MUST be short to run
                post: _postISI2   // this MUST be short to run
            });
            // response images
            trial_specs.push({
                urls: imgFiles[trialNumber][1],
                contexts: ctxs_test_on,
                duration: 0,              // immediately proceed to callback after paint
                pre: _preDrawResponse,    // this MUST be short to run
                post: _postDrawResponse   // this MUST be short to run
            });

            // Queue experiment
            dltk.queueTrial(trial_specs,
                function(hist, hist_delta) {
                    // now response images are up
                    var trialStartTime = new Date();
                    setTimeout(function() {
                        // schedule all less time critical jobs later here
                        var t_spent = dltk.getTimeSpent(hist);
                        var t_ISI1 = dltk.round2(t_spent[1]);
                        var t_stim = dltk.round2(t_spent[2]);
                        var t_ISI2 = dltk.round2(t_spent[3]);
                        var hist_extract = dltk.getTimingHistoryExcerpt(hist, 'diff');
                        var hist_delta_extract = dltk.getTimingHistoryExcerpt(hist_delta, 'diffeach');

                        var argdct = {
                            t_ISI1: t_ISI1, t_stim: t_stim, t_ISI2: t_ISI2,
                            hist_extract: hist_extract, hist_delta_extract: hist_delta_extract,
                            hist: hist, hist_delta: hist_delta,
                            trialStartTime: trialStartTime
                        };

                        exp.startClock();
                        _callHookfunctions('onResponseReady', argdct);

                        exp.setDebugMessage('ISI1, stimon, ISI2 = ' +
                            String(t_ISI1) + ', ' + String(t_stim) + ', ' + String(t_ISI2));
                    }, 0);
                },
                {rsrcs: rsrcs}
            );
        };

        var _primeSystemAndRunTrialOnce = function _primeSystemAndRunTrialOnce() {
            // Prime the browser by running a single blank trial
            var trial_specs = [];

            exp.stopClock();   // stop to minimize display burden

            // blank
            trial_specs.push({
                urls: [m.imgBlank],
                contexts: [ctx_sample_on],
                duration: 50,
                pre: _preISI1,    // this MUST be short to run
                //post: _postISI1   // this MUST be short to run
            });
            // another blank
            trial_specs.push({
                urls: [m.imgBlank],
                contexts: [ctx_sample_on],
                duration: 50,
                //pre: _preStim,    // this MUST be short to run
                //post: _postStim   // this MUST be short to run
            });
            // yet another blank
            trial_specs.push({
                urls: [m.imgBlank],
                contexts: [ctx_sample_on],
                duration: 50,
                //pre: _preISI2,    // this MUST be short to run
                //post: _postISI2   // this MUST be short to run
            });

            // Queue experiment
            dltk.queueTrial(trial_specs,
                function() {
                    setTimeout(function() {
                        // by now, the system has been primed.  Proceed to actual experiment.
                        primed = true;
                        _runTrialOnce();
                        exp.setDebugMessage('Primed.');
                    }, 0);
                },
                {rsrcs: rsrcs}
            );
        };

        var _safeRunTrialOnce = function _safeRunTrialOnce() {
            // This tries to ensure most optimal system performance by priming it when necessary
            if (!primed) _primeSystemAndRunTrialOnce();
            else _runTrialOnce();
        };

        var _clickedTestBtn = function _clickedTestBtn(index) {
            // Called when the turker clicks one of the test (answer) buttons
            var trialEndTime = new Date();
            var trialNumber = that.getCurrentTrialNumber();
            var trialInfo = that.getCurrentTrialInfo();
            var imgChosen = trialInfo.Sample[index];

            _callHookfunctions('onClickedTestBtn', 
                    {trialEndTime: trialEndTime, trialNumber: trialNumber,
                     trialInfo: trialInfo, imgChosen: imgChosen});
        };

        // -- Public methods
        this.init = function init() {
            // Initialize various RSVP related stuffs
            var arr, i;

            // imgFiles must be defined
            if (m.imgFiles === null || m.imgFiles.length === 0) {
                exp.setDebugMessage('init: "imgFiles" is not defined.');
                return false;
            }
            // shape must match
            if (m.imgFiles[0][1].length != m.elemTestCanvasIDs.length ||
                    m.elemTestCanvasIDs.length != m.elemTestClickables.length) {
                exp.setDebugMessage('init: "imgFiles[0][1]", "elemTestCanvasIDs", and "elemTestClickables" ' +
                        'have different shapes.');
                return false;
            }

            // on screen buffers for double buffering.
            // from: http://blog.bob.sh/2012/12/double-buffering-with-html-5-canvas.html
            ctx_sample_on = dltk.getOnScreenContextFromCanvas(m.elemSampleCanvasID);
            for (i = 0; i < m.elemTestCanvasIDs.length; i++)
                ctxs_test_on.push(dltk.getOnScreenContextFromCanvas(m.elemTestCanvasIDs[i]));

            that.totalTrials = m.imgFiles.length;
            that.trialNumber = -1;   // not yet started

            if (typeof(m.stimdurations) == 'number') {
                arr = [];
                for (i = 0; i < that.totalTrials; i++) arr.push(m.stimdurations);
                m.stimdurations = arr;
            }
            if (m.stimdurations.length != that.totalTrials) {
                exp.setDebugMessage('init: The length of "stimdurations" is not equal to "totalTrials".');
                return false;
            }
            
            if (typeof(m.ISIs) == 'number') {
                arr = [];
                for (i = 0; i < that.totalTrials; i++) arr.push(m.ISIs);
                m.ISIs = arr;
            }
            if (m.ISIs.length != that.totalTrials) {
                exp.setDebugMessage('init: The length of "ISIs" is not equal to "totalTrials".');
                return false;
            }

            $(m.elemSample).hide();
            $(m.elemTest).hide();
            return true;
        };

        this.getCurrentTrialInfo = function getCurrentTrialInfo() {
            // Returns the current info
            if (that.trialNumber < 0 || that.trialNumber >= that.totalTrials) return null;
            return {'Test': m.imgFiles[that.trialNumber][0], 'Sample': m.imgFiles[that.trialNumber][1]};
        };

        this.getCurrentTrialNumber = function getCurrentTrialNumber() {
            // Returns the current trial number
            return that.trialNumber;
        };

        this.setCurrentTrialNumber = function setCurrentTrialNumber(num) {
            if (num < -1 || num >= that.totalTrials) {
                exp.setDebugMessage('setCurrentTrialNumber: Invalid trialNumber');
                return false;
            }
            that.trialNumber = num;
            return true;
        };

        this.getTotalTrialNumber = function getTotalTrialNumber() {
            // Returns the current trial number
            return that.totalTrials;
        };

        this.onPreloadRsrcsAsync = function onPreloadRsrcsAsync(argdct) {
            // Preload resources.
            // This will be called when the system passes benchmark successfully by the Experiment object.
            // NOTE: This function MUST call argdct.finished() after loading all resources.  Otherwise,
            // the experiment will hang.

            // load fixation dot and blank image first...
            dltk.prepareResources(
                [[m.imgFixation, []], [m.imgBlank, []]], [ctx_sample_on, []],
                function() {
                    // ...then load trial images
                    dltk.prepareResources(
                        m.imgFiles, [ctx_sample_on, ctxs_test_on],
                        function () {       // call this when successfully proloaded all resources
                            argdct.finished();
                        },
                        function (progress, total) {
                            var argdct = {progress: progress, total: total, msg: ''};
                            _callHookfunctions('onUpdatePreloadProgress', argdct); 
                            $(o.elemPreload).html(argdct.msg);   // processed text is retrived from argdct.msg 
                        },
                        {rsrcs: rsrcs}
                    );
                },
                null,    // no progress update here
                {rsrcs: rsrcs});
            // Note: no need to call zen.preload() anymore
        };

        this.onBeginExp = function onBeginExp() {
            // Make the sample (answer) canvases clickable (This func is called by the Experiment object)
            var make_handler = function make_handler(idx) {
                return function () { _clickedTestBtn(idx); };
            };

            for (var i = 0; i < m.elemTestClickables.length; i++)
                $(m.elemTestClickables[i]).click(make_handler(i));
        };

        this.onRunNextTrial = function () {
            // this is called by Experiment object to procced to the next trial
            _safeRunTrialOnce();
        };

        this._updateOptions = function _updateOptions(optdctmodule) {
            // Provides an on-the-fly way to change some options
            // This is mainly provided for debugging/diagnosis purposes.
            // Be extra careful when use this; don't use unless you know what you're doing.
            if (!defined(optdctmodule)) return;
            m = dltk.applyDefaults(optdctmodule, m);
        };
    };  // end of RSVPModule

}(window.dltk = window.dltk || {}, window));
