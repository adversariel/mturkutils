/*!
 * dicarlo lab javascript toolkit
 */
(function (dltk, window) {
    // -- Some shortcut references to dltk.js
    var defined = dltk.defined;
    var callable = dltk.callable;
    var nop = dltk.nop;
    var round2 = dltk.round2;

    // -- Common code for Experiment and modules
    dltk.ERROR_DISABLED = 'disabled';
    dltk.ERROR_NOT_CALLABLE = 'not callable';
    dltk.CALLBACK_DEFAULT_SUFFIX = 'Default';
    dltk.CALLBACK_ASYNC_SUFFIX = 'Async';
    dltk._searchCallbackFunctions = function _searchCallbackFunctions(targets, flags, name) {
        // Finds all possible callback functions with ``name`` in ``targets``.
        // Functions will only be executed when the corresponding elements in ``flags`` are true.
        var jobs = [];
        for (var i = 0; i < targets.length; i++) {
            if (callable(targets[i][name])) {
                if (flags === true || flags[i])
                    jobs.push(targets[i][name]);
                else 
                    jobs.push(dltk.ERROR_DISABLED);
            }
            else
                jobs.push(dltk.ERROR_NOT_CALLABLE);
        }
        return jobs;
    };

    dltk._callCallbackFunctionsSyncOnly = function _callCallbackFunctionsSyncOnly(targets, flags, name, argdct) {
        var jobs_default = dltk._searchCallbackFunctions(targets, flags, name + dltk.CALLBACK_DEFAULT_SUFFIX);
        var jobs = dltk._searchCallbackFunctions(targets, flags, name);
        var results_default = dltk.runJobsSync(jobs_default, argdct);
        var results = dltk.runJobsSync(jobs, argdct);
        return {resultsSyncDefault: results_default, resultsSync: results};
    };

    dltk._callCallbackFunctions = function _callCallbackFunctions(targets, flags, name, argdct, onFinish) {
        var jobs_async_default = dltk._searchCallbackFunctions(targets, flags,
                name + dltk.CALLBACK_ASYNC_SUFFIX + dltk.CALLBACK_DEFAULT_SUFFIX);
        var jobs_async = dltk._searchCallbackFunctions(targets, flags, name + dltk.CALLBACK_ASYNC_SUFFIX);

        dltk.runJobsAsync(jobs_async_default, argdct, function (results_async_default) {
            // finished running all default async fns
            dltk.runJobsAsync(jobs_async, argdct, function (results_async) {
                // finished running all async fns
                var results = dltk._callCallbackFunctionsSyncOnly(targets, flags, name, argdct);
                if (callable(onFinish)) {
                    results.resultsAsyncDefault = results_async_default;
                    results.resultsAsync = results_async;
                    onFinish(results);
                }
            });
        });
    };

    // -- Main
    dltk.Experiment = function Experiment(_$, optdct) {
        /**********************************************************************
         This takes care of various experiment initialization and runs
         careful benchmarks. By using this, one can ensure that the turker's
         browser meets a set of predefined capabilities. It also provides a
         coherent way of attaching user-provided callback functions at
         various point of time. This itself does not provide any experimental
         paradigms (e.g., RSVP). To actually implement a task, one can attach
         various callback functions to work with the Experiment object,
         especially if the task design is very simple. However, for more
         involved tasks (e.g., RSVP), defining a module for the task and
         attaching it to Experiment is much more recommended since that will
         work with Experiemtn in a more integrated and cleaner way.

         Parameters:
         - _$: a reference to jquery
         - optdct: a dictionary that defines this experiment.
           See ``OPTDCT_DEFAULT`` below for possible options.
           (Better documentation TBD)
         **********************************************************************/

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
            /*** various callback functions ***/
            onAfterPassBenchmark: null,
            onPreloadRsrcs: null,
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
        var $ = function $(elem) {
            // safety wrapper to jquery: if no jquery is provided or the elemnt is missing
            // returns a wrapper that does nothing
            var target = defined(_$) ? _$(elem) : null;
            if (target === null || target.length === 0) {
                dltk.setDebugMessage('$: NOOP: ' + elem);
                return {hide: nop, show: nop, click: nop, html: nop, append: nop,
                    dialog: nop, css: nop, bind: nop};
            }
            return target;
        };

        // -- Public variables
        var o = dltk.applyDefaults(optdct, OPTDCT_DEFAULT);   // shorthand for optdct
        this.o = o;
        this.OS = dltk.BrowserDetect.OS;
        this.BROWSER = dltk.BrowserDetect.browser;

        this.exp_started = false;   // is experiment started?
        this.aID = dltk.getURLParameter(o.assignmentIDURLParameter);  // assignmentID
        this.benchmark_passed = false;
        this.benchmark_finished = false;
        this.benchmark = null;   // last benchmark
        this.benchmarks = [];    // all benchmark results
        this._timer_bench = null;
        this._timer_disp = null;
        this.modules = [];   // list of modules. Public, but ALMOST ALL THE CASES shouldn't be accessed directly
        // modules_isenabled: boolean list, where each elem determines if the module is enabled or not.
        // Enabled modules' callback functions will be called when necessary, whease disabled modules' not.
        this.modules_isenabled = [];
        // module_active: a index number that points to the current active module.  There is only one active module.
        // This is different from enable/disabled modules in that "module_active" is mainly used as a shortcut
        // to call getXXX() methods without actually specifying the module index.  See _callModule() for details.
        this.module_active = null;


        // -- Methods that form fundamentals of this class.  USERS DO NOT CALL THESE DIRECTLY.
        // -- They are public ONLY in order to make them overridable.
        this._callCallbackFunctions = function _callCallbackFunctions(name, argdct, onFinish) {
            // call all callback functions in enabled modules and optdct
            var targets = [o];
            var flags = [true];

            for (var i = 0; i < that.modules.length; i++) {
                targets.push(defined(that.modules[i].__optdct__) ? that.modules[i].__optdct__  : {});
                flags.push(that.modules_isenabled[i]);
            }

            dltk._callCallbackFunctions(targets, flags, name, argdct, onFinish);
        };

        this._callModule = function _callModule() {
            // (DO NOT ABUSE THIS: try to minimize use of this function.)
            // Call a module's method
            // Examples:
            // This calls "module_handle"-th module's theMethodToCall()
            //    _callModule(module_handle, 'theMethodToCall')  
            // This calls "module_handle"-th module's theMethodToCall() with an arguments  
            //    _callModule(module_handle, 'theMethodToCall', args...)
            // This calls the current active module's theMethodToCall()
            //    _callModule('theMethodToCall')
            //  Same, but passing arguments to the function
            //    _callModule('theMethodToCall', args...)
            var fn, module_handle, i, args = [];
            
            if (arguments.length === 0) return null;
            if (typeof(arguments[0]) == 'string') {
                // module_handle is omitted
                module_handle = that.module_active;
                fn = arguments[0];
                for (i = 0; i < arguments.length; i++) args.push(arguments[i]);
            }
            else if (arguments.length >= 2) {
                module_handle = (!defined(arguments[0]) || arguments[0] === null) ? that.module_active : arguments[0];
                fn = arguments[1];
                for (i = 2; i < arguments.length; i++) args.push(arguments[i]);
            }
            else return null;

            if (module_handle < 0 || module_handle >= that.modules.length) {
                dltk.setDebugMessage('_callModule: Invalid module_handle');
                return null;
            }

            if (!callable(that.modules[module_handle][fn])) {
                dltk.setDebugMessage('_callModule: not callable' + String(fn));
                return null;
            }
            return that.modules[module_handle][fn].apply(null, args);
        };

        this._callAllModules = function _callAllModules(fn, arg) {
            // Call all modules' fn with an argument arg
            var res = [];
            for (var i = 0; i < that.modules.length; i++) {
                res.push(that._callModule(i, fn, arg));
            }
            return res;
        };

        this._afterPassBenchmark = function _afterPassBenchmark() {
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

            that._callCallbackFunctions('onAfterPassBenchmark', {benchmarks: that.getBenchmarkResults()}, function() {
                if (!o.automaticallyRunPreloadAfterPassBenchmark)
                    return;
                var argdct = {elemPreload: o.elemPreload};
                // Call all preloaing routines one by one...
                that._callCallbackFunctions('onPreloadRsrcs', argdct, function () {
                    // finished all preloading....
                    that._callCallbackFunctions('onAfterPreloadAllModulesRsrcs', {}, function () {
                        // finished all post-preloading stuffs
                        if (o.automaticallyRunPreBeginExpAfterPreload)
                            that.preBeginExp();
                    });
                });
            });
        };

        this._checkSystem = function _checkSystem(benchmark) {
            // determine if this system is capable of running this task
            // based on the benchmark result
            var BROWSER = that.BROWSER;
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
            else that._afterPassBenchmark();
        };


        // -- Experimental methods that are public
        this.beginExp = function beginExp() {
            // This begins the experiment.
            // Called e.g. when Begin! button is clicked
            that.exp_started = true;
            $(o.elemBeginTaskBtn).hide();
            $(o.elemBeginTaskGroup).hide();
            $(o.elemPreload).hide();
            $(o.elemNotice).hide();
            that._callCallbackFunctions('onBeginExp', {}, function() {
                // All preps are done.  Run the first trial 
                if (o.automaticallyRunNextTrialOnBeginExp) that.runNextTrial();
            });
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

            dltk.runBenchmark(that._checkSystem, {canvas_test_fps: o.elemFPSBenchCanvasID,
                canvas_test_color: o.FPSBenchColor});   // run benchmark...
            that._timer_bench = setTimeout(function() {           // ... or fall back to failure mode in 1 min.
                that._checkSystem({api_support: false}); 
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

            if (o.elemTimer === null) return;
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

            that._callCallbackFunctions('onRecomputeOffset', {winW: winW, winH: winH,
                horizontal: horizontal, vertical: vertical,    // <- bad naming convention...
                offsetToTop: offsetToTop});
            dltk.setDebugMessage('recomputeOffset: Resized event detected:' + offsetToTop);
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
                dltk.setDebugMessage(o.msgNoMobile);
                return false;
            }
            if (o.supportedOS !== null && o.supportedOS.indexOf(that.OS) < 0) {
                msg = o.supportedOS.join(', ');
                pos = msg.lastIndexOf(', ');
                msg = (pos < 0) ? msg : msg.slice(0, pos) + ' and' + msg.slice(pos + 1);
                msg = o.msgNotSupportedOS.replace('${SUPPORTED_OS}', msg);

                $(o.elemWarning).show();
                $(o.elemWarning).append(msg);
                dltk.setDebugMessage(msg);
                return false;
            }
            if (o.supportedBrowser !== null && 
                    (o.supportedBrowser.indexOf(that.BROWSER) < 0 || !defined(vertical) || !defined(horizontal))) {
                msg = o.supportedBrowser.join(', ');
                pos = msg.lastIndexOf(', ');
                msg = (pos < 0) ? msg : msg.slice(0, pos) + ' or' + msg.slice(pos + 1);
                msg = o.msgNotSupportedBrowser.replace('${SUPPORTED_BROWSER}', msg);

                $(o.elemWarning).show();
                $(o.elemWarning).append(msg);
                dltk.setDebugMessage(msg);
                return false;
            }
            if (vertical < o.minVertical || horizontal < o.minHorizontal) {
                msg = o.msgScreenTooSmall;
                msg = msg.replace('${MINSZ}', String(o.minHorizontal) + 'x' + String(o.minVertical));

                $(o.elemWarning).show();
                $(o.elemWarning).append(msg);
                dltk.setDebugMessage(msg);
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
            dltk._printDbgMessage = o.printDbgMessage;   // somewhat crude but let's not worry for now

            return true;  // successful init
        };

        this.isStarted = function isStarted() {
            return that.exp_started;
        };

        this.runNextTrial = function runNextTrial() {
            // Proceed to the next trial
            if (!that.exp_started) return;
            var argdct = {stopClock: that.stopClock, startClock: that.startClock};
            that._callCallbackFunctions('onRunNextTrial', argdct);
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
            // Note: storing any other part of this calling Experiment object
            // in the module is discouraged because it can result in
            // difficult-to-manage code:
            var m = new module($, optdctmodule);
            if (!callable(m.init) || !m.init()) return -1;
            
            that.modules.push(m);
            that.modules_isenabled.push(true);
            if (that.modules.length != that.modules_isenabled.length) {
                dltk.setDebugMessage('addModule: modules.length != modules_isenabled.length');
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

        this.getCurrentTrialInfo = function getCurrentTrialInfo(module_handle) {
            // get the current trial info of the chosen module
            return that._callModule(module_handle, 'getCurrentTrialInfo');
        };

        this.getAllCurrentTrialInfo = function getAllCurrentTrialInfo() {
            // get the current trial info of all modules
            return that._callAllModules('getCurrentTrialInfo');
        };

        this.getCurrentTrialNumber = function getCurrentTrialNumber(module_handle) {
            // get the current trial # of the chosen module
            return that._callModule(module_handle, 'getCurrentTrialNumber');
        };

        this.getAllCurrentTrialNumbers = function getAllCurrentTrialNumbers() {
            // get the current trial numbers of all modules
            return that._callAllModules('getCurrentTrialNumber');
        };

        this.getTotalTrialNumber = function getTotalTrialNumber(module_handle) {
            // get the total trial # of the chosen module
            return that._callModule(module_handle, 'getTotalTrialNumber');
        };

        this.getAllTotalTrialNumbers = function getAllTotalTrialNumbers() {
            // get the total trial numbers of all modules
            return that._callAllModules('getTotalTrialNumber');
        };

        this.setCurrentTrialNumber = function setCurrentTrialNumber(num, module_handle) {
            // Sets the current trialNumber of "module_handle"-th module.
            return that._callModule(module_handle, 'setCurrentTrialNumber', num);
        };
    };  // end of Experiment
}(window.dltk = window.dltk || {}, window));
