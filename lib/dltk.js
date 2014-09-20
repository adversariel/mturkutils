/*!
 * dicarlo lab javascript toolkit
 * This file contains basic graphics and utility functions
 */
(function (dltk, window) {
    /*************************************************************************
     * Common variables / constants                                          *
     *************************************************************************/
    dltk.STATLEN = 2;                 // minimum length to compute statistics
    dltk.SLOPPY = 5;                  // the amount of shortfall in setTimeout2
    dltk.EPS = 2;                     // slack time in setTimeout2
    dltk.BOGO_MIPS_TOL = 1;           // Computer should be faster than 1 BogoMIPS
    dltk.JS_TRES_TOL = 17;            // An example tolerance value for js timing (~60Hz frame rate)
    dltk.JS_TRES_VAR_TOL = 10;         // this much of variation deemed fine
    dltk.FRAME_INTERVAL_TOL = 1000 / 60 + 2;   // mean frame interval should be smaller than 16.66ms + 2ms
    dltk.FRAME_INTERVAL_VAR_TOL = 10;          // jitter shouldn't be larger than this
    dltk.FRAME_INTERVAL_QUANTFAC_TOL = 0.8;    // fail if more than 80% of timestamps are multiples of 100us (FF)
    dltk.FRAME_INTERVAL_UNIQFAC_TOL = 3;       // fail if there are <= 3 unique intervals (Chrome)
    dltk.STATLEN_FPS = 6;             // use last six frames to figure out current fps

    dltk.preloaded_rsrcs = {};        // a dictionary of on/off screen contexts + etc. for preloaded imgs

    dltk.js_tres = null;              // setTimeout resolution...
    dltk.js_tres_variance = null;     // ...and variance
    dltk.bogoMIPS = null;             // same as the name
    dltk.refresh_test_timestamps = null;
    dltk.refresh_interval = null;

    dltk._jobs = [];                  // functions to be called sequentially and asynchronously
    dltk.ERROR_NOT_CALLABLE = 'not callable';

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
    dltk.callable = function callable(obj) {
        return typeof(obj) == 'function';
    };
    var callable = dltk.callable;

    dltk.defined = function defined(obj) {
        return typeof(obj) != 'undefined';
    };
    var defined = dltk.defined;

    dltk._debugMsg = '';
    dltk._printDbgMessage = false;
    dltk.setDebugMessage = function setDebugMessage(msg) {
        dltk._debugMsg = msg;
        if (dltk._printDbgMessage) window.console.log(msg);
    };

    dltk.getDebugMessage = function getDebugMessage() {
        return dltk._debugMsg;
    };

    dltk.error = function error(msg, diagnostic_info) {
        return {__error__: msg, __diagnostic_info__: diagnostic_info};
    };

    dltk.toMicrosec = function (x) { return parseInt(Math.round(x * 1000), 10); };
    var toMicrosec = dltk.toMicrosec;

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

    dltk.copydct = function copydct(src, excludes) {
        // Returns a shallow copy of ``src`` dictionary. One can optionally
        // pass an array ``excludes`` that lists keys to be excluded.
        var dst = {};
        var excl = defined(excludes) ? excludes : [];

        for (var k in src) {
            if (src.hasOwnProperty(k) && excl.indexOf(k) < 0) {
                dst[k] = src[k];
            }
        }
        return dst;
    };
    var copydct = dltk.copydct;

    var __apply_queue = [];   // functions and arguments to be processed.
    dltk.__apply_queue = __apply_queue;   // debug purposes only!!

    var __apply_inner = function __apply_inner() {
        // The next job to be processed: pops the current 0-th element
        var fnargsctx = __apply_queue.splice(0, 1)[0];
        if (!defined(fnargsctx)) {
            dltk.setDebugMessage('dltk.__apply_inner: unmatched call');
            return;
        }

        var fn = fnargsctx[0];
        var args = fnargsctx[1];
        var ctx = fnargsctx[2];
        fn.apply(ctx, args);
    };

    dltk._apply = function _apply(fn, args, context, delay) {
        // This "applies" args to fn()  in the global context
        // with a help of setTimeout(0) in order to avoid accumulation of
        // variable search contexts.
        var ctx = defined(context) ? context : null;
        var d = defined(delay) ? delay : 0;
        __apply_queue.push([fn, args, ctx]);
        setTimeout(__apply_inner, d);
    };
    var _apply = dltk._apply;

    dltk.runJobsAsync = function runJobsAsync(jobs, argdct, onFinish) {
        // Run a list of functions ``jobs`` asynchronously one by one by passing ``argdct``.
        // If ``jobs`` is undefined, dltk._jobs will be used instead (not recommended).
        // All functions in the queue ``jobs`` MUST call argdct.finished()
        // upon completetion of its task, otherwise this call system will hang.
        // One can optionally pass an object argument to argdct.finished(),
        // which will be stored internally.  ``onFinish()`` will be called
        // (if provded) when all ``jobs`` are completed.  It will be called with
        // a list of the objects that were passed with argdct.finished()
        var _jobs = defined(jobs) ? jobs : dltk._jobs;
        var fn, arg, src;
        
        if (!defined(argdct) || typeof(argdct) != 'object') {
            arg = {};
            arg.__protected__ = {};
        }
        else {
            // this keeps the original copy
            if (defined(argdct.__protected__))
                src = argdct.__protected__;
            else
                src = argdct;

            arg = copydct(src, ['__results__']);
            arg.__protected__ = copydct(src);
            // ^ this keeps a copy of original argdct and reduces unintended overwriting
        }

        if (!defined(arg.__protected__.__results__))
            arg.__protected__.__results__ = [];   // results of callback functions
        if (arg.hasOwnProperty('__this_result__'))
            arg.__protected__.__results__.push(arg.__this_result__);

        if (!defined(arg.__protected__.job_index))
            arg.__protected__.job_index = -1;     // meaning before execution any

        if (!defined(_jobs) || _jobs.length === 0) {
            // finished!!
            if (callable(onFinish))
                _apply(onFinish, [arg.__protected__.__results__]);
            return;   // done
        }

        fn = _jobs.splice(0, 1)[0];   // function to call: pops the current 0-th element
        arg.finished = function _runJobsAsync_inner(resultdct) {
            arg.__protected__.__this_result__ = resultdct;
            // proceed to the next job
            _apply(runJobsAsync, [_jobs, arg, onFinish]);
            // unsubscribe to help GC
            _jobs = null;
            arg = null;
            onFinish = null;
        };
        arg._timestamp = performance.now();
        arg._job_index = ++arg.__protected__.job_index;

        if (callable(fn))
            fn(arg);
        else
            arg.finished(dltk.error(dltk.ERROR_NOT_CALLABLE, fn));
    };

    dltk.runJobsSync = function runJobsSync(jobs, argdct) {
        // Run a list of functions ``jobs`` in the current context (JavaScript jargon
        // "synchronously") one by one by passing ``argdct``.
        // A list that contains the results of ``jobs`` will be returned.
        var _jobs = defined(jobs) ? jobs : dltk._jobs;
        var res = [], r, arg;
        
        for (var i = 0; i < _jobs.length; i++) {
            if (typeof(argdct) != 'object') {
                arg = {__protected__: {}};
            }
            else {
                arg = copydct(argdct);
                arg.__protected__ = argdct;
            }
            // ^ this keeps the original argdct separate and reduces unintended overwriting
            // and crosstalk between jobs.

            arg._timestamp = performance.now();
            arg._job_index = i;
            if (callable(_jobs[i]))
                r = _jobs[i](arg);
            else
                r = dltk.error(dltk.ERROR_NOT_CALLABLE, _jobs[i]);
            res.push(r);   // save results
        }
        return res;
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

    dltk.applyDefaults = function applyDefaults(paramdct, defaultdct) {
        if (!defined(paramdct)) return defaultdct;
        for (var k in defaultdct) {
            if (!defined(paramdct[k])) paramdct[k] = defaultdct[k];
        } 
        return paramdct;
    };
    var applyDefaults = dltk.applyDefaults;

    dltk.roundNDecimal = function roundNDecimal(num, n) {
        n = parseInt(n, 10);
        var m = Math.pow(10, n);
        return Math.round(num * m) / m;
    };

    dltk.round2 = function round2(num) {
        return dltk.roundNDecimal(num, 2);
    };

    dltk.nop = function () { };   // function that does nothing

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
    dltk._setTimeout2Cnt = 0;  // debugging purposes only. do not rely on this variable.
    dltk._setTimeout2_inner = function _setTimeout2_inner(delay, t0, fn) {
        dltk._setTimeout2Cnt = 0;
        while(performance.now() - t0 < delay - dltk.EPS) dltk._setTimeout2Cnt++;
        fn();
    };

    dltk.setTimeout2 = function setTimeout2(fn, delay) {
        // A function similar to setTimeout but much more accurate
        // NOTE: however this does NOT guarantee actual redrawing of the
        // screen by the browser.
        var t0 = performance.now(), sloppy_delay;
        dltk._setTimeout2Cnt = 0;
        if (dltk.js_tres !== null)
            sloppy_delay = delay - dltk.js_tres * dltk.SLOPPY;
        else
            sloppy_delay = delay - 50;

        if (sloppy_delay <= 0) dltk._setTimeout2_inner(delay, t0, fn);
        else _apply(dltk._setTimeout2_inner, [delay, t0, fn], null, sloppy_delay);
    };

    dltk.getDriftCompensation = function getDriftCompensation(time_spent, prev_biases, ref) {
        // Simple function that estimates obtimal bias to attain time delay of "ref"
        // based on previously measured history of "time_spent" and "prev_biases"
        return time_spent.length >= dltk.STATLEN ? time_spent.mean() + prev_biases.mean() - ref : 0;
    };

    dltk.measureTimeResolution = function measureTimeResolution(callback, duration) {
        // Measures the minimum time resolution that can be attained by setTimeout(fn, 0)
        var DUR_DEFAULT = 400;   // run for 400 counts by default
        var DUR = (!dltk.defined(duration) ? DUR_DEFAULT : duration);
        var jobs = [];

        var measureTimeResolution_inner = function measureTimeResolution_inner(argdct) {
            argdct.finished(performance.now());
        };

        var measureTimeResolution_done = function measureTimeResolution_done(results) {
            var diff = results.diff();
            dltk.js_tres = Math.max(diff.mean(), 0);
            dltk.js_tres_variance = diff.variance();
            if (dltk.callable(callback))
                dltk._apply(callback, [dltk.js_tres, dltk.js_tres_variance]);
            callback = null;    // to help GC
        };

        for (var i = 0; i < DUR; i++)
            jobs.push(measureTimeResolution_inner);

        dltk.runJobsAsync(jobs, {}, measureTimeResolution_done);
    };

    dltk.measureBogoMIPS = function measureBogoMIPS(callback, reps) {
        // Measures more accurate BogoMIPS by making several measurements
        var REPS_DEFAULT = 3;
        var REPS = (!dltk.defined(reps) ? REPS_DEFAULT : reps);
        var jobs = [];

        var measureBogoMIPSOnce = function measureBogoMIPSOnce(duration) {
            // Measures BogoMIPS just once
            // from: http://www.pothoven.net/javascripts/src/jsBogoMips.js
            var t0 = performance.now();
            var loops_per_sec = 0 + 0;
            var t1 = performance.now();
            var compensation = t1 - t0;
            var DUR_DEFAULT = 500;   // run for 500ms by default
            var DUR = (!dltk.defined(duration) ? DUR_DEFAULT : duration);
            var tend = performance.now() + DUR;

            while (t1 < tend) {
                loops_per_sec++;
                t1 = performance.now();
            }

            return (loops_per_sec + (loops_per_sec * compensation)) / (1000000 / (1000 / DUR));
        };

        var measureBogoMIPS_inner = function measureBogoMIPS_inner(argdct) {
            argdct.finished(measureBogoMIPSOnce());
        };

        var _measureBogoMIPS_done = function _measureBogoMIPS_done(results) {
            dltk.bogoMIPS = results.mean();
            if (dltk.callable(callback))
                dltk._apply(callback, [dltk.bogoMIPS]);
            callback = null;    // to help GC
        };

        for (var i = 0; i < REPS; i++)
            jobs.push(measureBogoMIPS_inner);

        dltk.runJobsAsync(jobs, {}, _measureBogoMIPS_done);
    };

    dltk.measureScreenRefreshInterval = function measureScreenRefreshInterval(canvas, callback, test_color, reps) {
        var REPS_DEFAULT = 120;
        var REPS = (!dltk.defined(reps) ? REPS_DEFAULT : reps);
        var COLOR_DEFAULT = '#7f7f7f';
        var COLOR = (!dltk.defined(test_color) ? COLOR_DEFAULT : test_color);
        var ctx = dltk.getOnScreenContextFromCanvas(canvas);
        var timestamps = [];

        // this tries to detect bad states in browsers on Windows
        // especially after the computer wakes up from a sleep.
        // "Bad" timestamps are almost always exact multiples of 100us
        // (and typically multiples of 1000us).
        var isquantized = function (x) { return (toMicrosec(x) % 100 === 0) ? 1 : 0; };
        var isvalidunique = function (x) { return (x >= 15 && x <= 18) ? 1 : 0; };

        // actual measurements are made here
        var measureScreenRefreshIntervals_inner = function measureScreenRefreshIntervals_inner(ts) {
            dltk.drawToContext('color:' + COLOR, ctx);
            timestamps.push(ts);

            if (timestamps.length >= REPS) {
                // finished testing
                dltk.refresh_test_timestamps = timestamps;
                dltk.refresh_interval = timestamps.mean();
                if (dltk.callable(callback)) {
                    var quantization_factor = timestamps.map(isquantized).mean();
                    var uniqueness_factor = timestamps.diff().getUnique().map(isvalidunique).sum();

                    dltk._apply(callback, [timestamps.diff().mean(), timestamps.diff().variance(),
                        quantization_factor, uniqueness_factor], null, 100);
                }
                // GC stuffs:
                timestamps = null;
                ctx = null;
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
        var bench_jobs = [];
        bench_jobs.push(function(argdct) {
            dltk.measureTimeResolution.bind({})(function (js_tres, js_tres_variance) {
                result.js_tres = js_tres;
                result.js_tres_variance = js_tres_variance;
                argdct.finished();
            }, tres_dur);
        });
        bench_jobs.push(function(argdct) {
            dltk.measureBogoMIPS.bind({})(function (mips) {
                result.bogoMIPS = mips;
                argdct.finished();
            }, mips_reps);
        });
        bench_jobs.push(function(argdct) {
            if (!defined(canvas_test_fps)) {
                argdct.finished();
                return;   // do not delete this line.
            }
            dltk.measureScreenRefreshInterval.bind({})(canvas_test_fps,
                function(refresh_interval, refresh_interval_variance, quantization_factor, uniqueness_factor) {
                    result.refresh_interval = refresh_interval;
                    result.refresh_interval_variance = refresh_interval_variance;
                    result.refresh_interval_quantization_factor = quantization_factor;
                    result.refresh_interval_uniqueness_factor = uniqueness_factor;
                    argdct.finished();
                }, canvas_test_color);
        });
        bench_jobs.push(function(argdct) {
            // measure this once again
            dltk.measureTimeResolution.bind({})(function (js_tres, js_tres_variance) {
                result.js_tres = Math.max(js_tres, result.js_tres);
                result.js_tres_variance = Math.max(js_tres_variance, result.js_tres_variance);
                argdct.finished();
            }, tres_dur);
        });
        dltk.runJobsAsync(bench_jobs, {}, function () {
            if (callable(callback))
                _apply(callback, [result]);
            result = null;
        });
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

            if (callable(callback)) setTimeout(function() {
                callback(t_draw_begin);
                t_draw_begin = null;
                callback = null;
            }, 0);
            // ^ use setTimeout to ensure callback() is called later than this function.
        }
        else {
            img =  new Image();
            img.onload = function() {
                ctx.drawImage(img, 0, 0, w, h);  // should stretch
                //ctx.drawImage(img, 0, 0);

                // if callback is requested...
                if (callable(callback)) callback(t_draw_begin);

                // GC related stuffs:
                callback = null;
                t_draw_begin = null;
                ctx = null;
                img.onload = null;   // trying to be explicit 
                img = null;
            };
            img.src = imgurl;
        }
        return t_draw_begin;
    };

    dltk.copyContexts = function copyContexts(ctxsrc, ctxdst) {
        ctxdst.drawImage(ctxsrc.canvas, 0, 0);
    };
    var copyContexts = dltk.copyContexts;

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
        optdct = applyDefaults(optdct, optdct_default);
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
        var jobs = [], urls = [], ctxs = [], elemIdx = [];
        var numElems = imgFiles.length;
        var flatOnScrContexts = onScrContexts.flatten();
        var sanitizedProgressfn = callable(progressfn) ? progressfn : dltk.nop;

        var prepareResources_inner = function prepareResources_inner(argdct) {
            // no closure here, yay!
            var idx = argdct._job_index;
            dltk.prepareResourcesOnce(argdct.urls[idx], argdct.ctxs[idx], argdct.finished, argdct.optdct);
            argdct.progressfn(argdct.elemIdx[idx], argdct.numElems);
        };

        for (var i = 0; i < numElems; i++) {
            var flatThisElem = imgFiles[i].flatten();
            var numFlatThisElem = flatThisElem.length;

            for (var j = 0; j < numFlatThisElem; j++) {
                urls.push(flatThisElem[j]);
                ctxs.push(flatOnScrContexts[j]);
                jobs.push(prepareResources_inner);
                elemIdx.push(i);
            }
        }

        dltk.runJobsAsync(jobs, {urls: urls, ctxs: ctxs, optdct: optdct,
            elemIdx: elemIdx, numElems: numElems,
            progressfn: sanitizedProgressfn}, callback);
    };

    // queueTrial related --- rewritten in this form to minimize fn redefining and mem leak
    var qt_running = false;
    var qt_t0, qt_te;
    var qt_specs;
    var qt_callback;
    var qt_idx;                 // current index of components
    var qt_history, qt_history_delta, qt_history_delta_flush;
    var qt_tstamps, qt_tstamps_all, qt_tdeltas, qt_tdeltaflushes;
    var qt_optdct;
    var qt_measureFlushTiming;
    var qt_flush_duration = function qt_flush_duration() {
        qt_tdeltaflushes.push(performance.now() - qt_te);
    };
    var qt_statlen_fps;

    var qt_render = function qt_render(t) {
        // NOTE: this part is highly hand-optimized. Please be very careful
        // when modify this.

        // re-define often used closure vars as local for scoping efficiency
        // DONT FORGET TO UPDATE THE CLOSURE VARS WHEN NECESSARY
        var specs = qt_specs;
        var this_spec;
        var idx = qt_idx;
        var t0 = qt_t0;
        var tstamps = qt_tstamps;
        var tstamps_all = qt_tstamps_all;
        var tdeltas = qt_tdeltas;
        var w, h, ctx, url, ctxs, urls, t_interval, l, te;
        tstamps.push(t);
        tstamps_all.push(t);
        t_interval = tstamps_all.slice(-(qt_statlen_fps + 1)).diff().mean();

        // -- no need to update the screen
        if (idx >= 0) {
            // half-frame jitter is okay and probably unavoidable
            if ((t - t0) < (specs[idx].duration - t_interval / 2)) {
                // no drawing, done for now
                te = qt_te = performance.now();
                tdeltas.push(te - t);
                window.requestAnimationFrame(qt_render);
                qt_measureFlushTiming();
                return;
            }
        }

        // -- update the screen
        var history = qt_history;
        var history_delta = qt_history_delta;
        var history_delta_flush = qt_history_delta_flush;
        var tdeltaflushes = qt_tdeltaflushes;
        var rsrcs = qt_optdct.rsrcs;

        idx = ++qt_idx;
        this_spec = specs[idx];
        history.push(tstamps);
        history_delta.push(tdeltas);
        history_delta_flush.push(tdeltaflushes);
        qt_t0 = t0 = t;
        qt_tstamps = tstamps = [t0];
        qt_tdeltas = tdeltas = [];
        qt_tdeltaflushes = tdeltaflushes = [];

        // finished?
        if (idx >= specs.length) {
            if (callable(qt_callback)) qt_callback(history, history_delta, history_delta_flush);
            qt_running = false;
            return;
        }

        // do necessary setups prior to draw idx-th component
        if (callable(this_spec.pre)) this_spec.pre(history, history_delta, history_delta_flush);

        // render
        urls = this_spec.urls;
        ctxs = this_spec.contexts;   // on-screen contexts
        l = urls.length;
        for (var j = 0; j < l; j++) {
            url = urls[j];
            ctx = ctxs[j];
            w = ctx.canvas.width;
            h = ctx.canvas.height;
            // transfer preloaded image to ctx: should be fast
            copyContexts(rsrcs[url][[w, h]], ctx);
        }

        // do necessary interventions after drawing of idx-th component
        if (callable(this_spec.post)) this_spec.post(history, history_delta, history_delta_flush);

        qt_te = te = performance.now();
        tdeltas.push(te - t);
        window.requestAnimationFrame(qt_render);
        qt_measureFlushTiming();
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
        //

        if (qt_running) {
            dltk.setDebugMessage('dltk.queueTrial: already running.');
            return;
        }
        qt_running = true;

        var optdct_default = {rsrcs: dltk.preloaded_rsrcs, measureFlushTiming: false};

        qt_optdct = applyDefaults(optdct, optdct_default);
        qt_t0 = qt_te = performance.now();
        qt_idx = -1;
        qt_history = [];
        qt_history_delta = [];
        qt_history_delta_flush = [];
        qt_tstamps = [];
        qt_tstamps_all = [];
        qt_tdeltas = [];
        qt_tdeltaflushes = [];
        qt_specs = specs;
        qt_callback = callback;
        qt_statlen_fps = dltk.STATLEN_FPS;

        if (qt_optdct.measureFlushTiming) {
            qt_measureFlushTiming = function () {
                setTimeout(qt_flush_duration, 0);
            };
        }
        else
            qt_measureFlushTiming = dltk.nop;

        window.requestAnimationFrame(qt_render);
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

    window.String.prototype.endsWith = function(suffix) {
        // http://stackoverflow.com/questions/280634/endswith-in-javascript
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };
}(window.dltk = window.dltk || {}, window));
