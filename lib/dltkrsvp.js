/*!
 * dicarlo lab javascript toolkit
 */
(function (dltk /*, window -- commented as unused */) {
    // -- Some shortcut references to dltk.js
    var callable = dltk.callable;
    var defined = dltk.defined;
    var setDebugMessage = dltk.setDebugMessage;

    // -- Standard RSVP
    dltk.RSVPModule = function RSVPModule(_$, optdct) {
        /**********************************************************************
         This is a module class that provides the "standard" RSVP
         sample-and-test experimental paradigm. This uses the new dltk graphics
         framework and delivers much more precise presentation time control.
         As a module, this is designed to be used with dltk.Experiment; i.e.,
         not to be used called directly by the user.

         Parameters:
         - _$: a reference to jquery
         - optdct: dictionary that contains options for this RSVP module.
           See ``OPTDCT_DEFAULT`` below for deails.
           (Better documentation TBD)

         Note: storing any other part of the calling Experiment object is
         discouraged because it can result in difficult-to-manage code.
         **********************************************************************/

        // -- Default constants
        var MSG_TRIAL_PROGRESS = 'Progress:<br /> ${CURRENT} of ${TOTAL}';
        var IMG_FIXATION = 'https://s3.amazonaws.com/task_images/fixation_360x360.png';
        var IMG_BLANK = 'https://s3.amazonaws.com/task_images/blank_360x360.png';

        var OPTDCT_DEFAULT = {
            /******* basic setup vars **********/
            elemSample: null, elemTest: null,   // html elems that fully contain sample and test stuffs respectively
            elemSampleCanvasID: null,  // canvas id to which the RSVP stimuli will be painted on. do not prepend #
            elemTestCanvasIDs: null,   // canvas ids for ans choices. must match the shape of spec.Test. dont prepend #
            elemTestClickables: null,  // elements that will be made clickable to receive answers
            elemTrialCounter: null,
            /******** callback functions: these MUST be short to run (ideally less than 2ms) ***********/
            // all of the following drawing related callbacks (onPreXXX, onPostXXX)
            // MUST be short to execute (ideally less than few ms)
            onPreISI1Default: '_onPreISI1Default',   // pass null to disable this
            onPreISI1: null,
            onPostISI1: null,
            onPreStim: null,
            onPostStim: null,
            onPreISI2: null,
            onPostISI2: null,
            onPreDrawResponseDefault: '_onPreDrawResponseDefault',   // pass null to disable this
            onPreDrawResponse: null,
            onPostDrawResponse: null,
            // other task related callbacks
            onResponseReadyAsync: null,
            onResponseReady: null,
            onClickedTestBtnAsync: null,
            onClickedTestBtn: null,
            // the followings are called by Experiment
            onPreloadRsrcsAsyncDefault: '_onPreloadRsrcsAsyncDefault',  // pass null to disable this
            onPreloadRsrcsAsync: null,
            onBeginExpDefault: '_onBeginExpDefault',                    // pass null to disable this
            onBeginExp: null,
            onRunNextTrialAsyncDefault: '_onRunNextTrialAsyncDefault',  // pass null to disable this
            onRunNextTrialAsync: null,
            /******** other options ***********/
            useLocalTrialNumbersForDisplay: true,  // use local trial numbers for display purposes? (e.g., trial progress)
            stopClockBeforeSample: true,
            startClockAfterSample: true,
            optdctQueueTrial: {},      // options to be passed to dltk.queueTrial(), except rsrcs -- see init()
            /******** text constants **********/
            msgTrialProgress: MSG_TRIAL_PROGRESS,
            imgFixation: IMG_FIXATION,
            imgBlank: IMG_BLANK,
        };

        // -- Private variables
        var that = this;
        var primed = false;
        var testing_period = false;   // buttons are only responsive during the testing period

        // -- Public variables
        var o = dltk.applyDefaults(optdct, OPTDCT_DEFAULT);
        this.o = o;            // Make this public in case for overriding
        this.__optdct__ = o;   // This is required by Experiment

        this.ctx_sample_on = null;
        this.ctxs_test_on = [];
        this.rsrcs = {};       // preloaded resources goes to here, not to the dltk.preloaded_rsrcs

        this.currentTrialInfo = null;   // current trial info


        // -- Methods that form fundamentals of this class.  USERS DO NOT CALL THESE DIRECTLY.
        // -- They are public ONLY in order to make them overridable.
        this._callCallbackFunctionsSyncOnly = function _callCallbackFunctionsSyncOnly(name, argdct) {
            return dltk._callCallbackFunctionsSyncOnly([o], true, name, argdct);
        };
        this._callCallbackFunctions = function _callCallbackFunctions(name, argdct, onFinish) {
            return dltk._callCallbackFunctions([o], true, name, argdct, onFinish);
        };

        this._getPreloadProgressText = function _getPreloadProgressText(argdct) {
            var progress = argdct.progress, total = argdct.total;
            var msg = "<font color=red style=background-color:white><b>Processing resources: " +
                progress + "/" + total + "</b></font>";
            return msg;
        };

        this.__argdct_ui__ = {};
        this._preISI1 = function _preISI1() {
            that._callCallbackFunctionsSyncOnly('onPreISI1', that.__argdct_ui__);
        };
        this._postISI1 = function _postISI1() {
            that._callCallbackFunctionsSyncOnly('onPostISI1', that.__argdct_ui__);
        };
        this._preStim = function _preStim() {
            that._callCallbackFunctionsSyncOnly('onPreStim', that.__argdct_ui__);
        };
        this._postStim = function _postStim() {
            that._callCallbackFunctionsSyncOnly('onPostStim', that.__argdct_ui__);
        };
        this._preISI2 = function _preISI2() {
            that._callCallbackFunctionsSyncOnly('onPreISI2', that.__argdct_ui__);
        };
        this._postISI2 = function _postISI2() {
            that._callCallbackFunctionsSyncOnly('onPostISI2', that.__argdct_ui__);
        };
        this._preDrawResponse = function _preDrawResponse() {
            that._callCallbackFunctionsSyncOnly('onPreDrawResponse', that.__argdct_ui__);
        };
        this._postDrawResponse = function _postDrawResponse() {
            that._callCallbackFunctionsSyncOnly('onPostDrawResponse', that.__argdct_ui__);
        };

        this._getRSVPTrialSpecs = function _getRSVPTrialSpecs(argdct) {
            // Returns a spec for "standard" RSVP tasks
            var trial_specs = [];
            var ctx_sample_on = that.ctx_sample_on;
            var ctxs_test_on = that.ctxs_test_on;
            var c = argdct.trialInfo;
            var ISI = c.ISI;
            var stimdur = c.SampleDuration;
            var sampleURL = c.Sample;
            var testURLs = c.Test;

            that.__argdct_ui__ = {ctx_sample_on: ctx_sample_on, ctxs_test_on: ctxs_test_on,
                trialInfo: c};

            // ISI 1 fixation dot
            trial_specs.push({
                urls: [o.imgFixation],
                contexts: [ctx_sample_on],
                duration: ISI,
                pre: that._preISI1,    // this MUST be short to run
                post: that._postISI1   // this MUST be short to run
            });
            // sample stimulus
            trial_specs.push({
                urls: [sampleURL],
                contexts: [ctx_sample_on],
                duration: stimdur,
                pre: that._preStim,    // this MUST be short to run
                post: that._postStim   // this MUST be short to run
            });
            // ISI 2 blank
            trial_specs.push({
                urls: [o.imgBlank],
                contexts: [ctx_sample_on],
                duration: ISI,
                pre: that._preISI2,    // this MUST be short to run
                post: that._postISI2   // this MUST be short to run
            });
            // response images
            trial_specs.push({
                urls: testURLs,
                contexts: ctxs_test_on,
                duration: 0,              // immediately proceed to callback after paint
                pre: that._preDrawResponse,    // this MUST be short to run
                post: that._postDrawResponse   // this MUST be short to run
            });
            return trial_specs;
        };

        this._getTimingAnalysisResults = function _getTimingAnalysisResults(hist, hist_delta, hist_delta_flush) {
            var t_spent = dltk.getTimeSpent(hist);
            var t_ISI1 = dltk.round2(t_spent[1]);
            var t_stim = dltk.round2(t_spent[2]);
            var t_ISI2 = dltk.round2(t_spent[3]);
            var hist_extract = dltk.getTimingHistoryExcerpt(hist, 'diff');
            var hist_delta_extract = dltk.getTimingHistoryExcerpt(hist_delta, 'diffeach');
            var diag = 'ISI1, stimon, ISI2 = ' + String(t_ISI1) + ', ' + String(t_stim) + ', ' + String(t_ISI2);
            return {
                t_ISI1: t_ISI1, t_stim: t_stim, t_ISI2: t_ISI2, t_spent_all: t_spent,
                hist_extract: hist_extract, hist_delta_extract: hist_delta_extract,
                hist: hist, hist_delta: hist_delta, hist_delta_flush: hist_delta_flush,
                __diag_msg__: diag,
            };
        };

        this._runTrialOnce = function _runTrialOnce(argdct) {
            if (o.stopClockBeforeSample) argdct.stopClock();   // stop to minimize display burden

            // Queue experiment
            dltk.queueTrial(that._getRSVPTrialSpecs(argdct),     // this function returns the rendering specs
                function(hist, hist_delta, hist_delta_flush) {
                    // now response images are up
                    var trialStartTime = new Date();
                    setTimeout(function() {
                        // schedule all less time critical jobs later here
                        if (o.startClockAfterSample) argdct.startClock();

                        var argdct_timing = that._getTimingAnalysisResults(hist, hist_delta, hist_delta_flush);
                        argdct_timing.trialStartTime = trialStartTime;
                        that._callCallbackFunctions('onResponseReady', argdct_timing, argdct.finished);
                        // MUST call this to avoid experiment hang -------------------^

                        // GC
                        hist = null;
                        hist_delta = null;
                        hist_delta_flush = null;
                        trialStartTime = null;
                        argdct = null;
                        dltk.setDebugMessage(argdct_timing.__diag_msg__);
                    }, 0);
                },
                o.optdctQueueTrial
            );
        };

        this._primeSystemAndRunTrialOnce = function _primeSystemAndRunTrialOnce(argdct) {
            // Prime the browser by running a single blank trial
            var trial_specs = [];
            var ctx_sample_on = that.ctx_sample_on;
            var ctxs_test_on = that.ctxs_test_on;

            if (o.stopClockBeforeSample) argdct.stopClock();   // stop to minimize display burden

            that.__argdct_ui__ = {ctx_sample_on: ctx_sample_on, ctxs_test_on: ctxs_test_on,
                trialInfo: argdct.trialInfo};

            // blank
            trial_specs.push({
                urls: [o.imgBlank],
                contexts: [ctx_sample_on],
                duration: 50,
                pre: that._preISI1,    // this MUST be short to run
                //post: _postISI1   // this MUST be short to run
            });
            // another blank
            trial_specs.push({
                urls: [o.imgBlank],
                contexts: [ctx_sample_on],
                duration: 50,
                //pre: _preStim,    // this MUST be short to run
                //post: _postStim   // this MUST be short to run
            });
            // yet another blank
            trial_specs.push({
                urls: [o.imgBlank],
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
                        that._runTrialOnce(argdct);
                        dltk.setDebugMessage('Primed.');
                        argdct = null;   // GC stuff
                    }, 0);
                },
                o.optdctQueueTrial
            );
        };

        this._safeRunTrialOnce = function _safeRunTrialOnce(argdct) {
            // This tries to ensure most optimal system performance by priming it when necessary
            if (!primed) that._primeSystemAndRunTrialOnce(argdct);
            else that._runTrialOnce(argdct);
        };

        this._clickedTestBtn = function _clickedTestBtn(index) {
            // Called when the turker clicks one of the test (answer) buttons
            var trialInfo, trialEndTime, imgChosen, res;
            testing_period = false;    // disable buttons until next testing period
            trialInfo = that.getCurrentTrialInfo();
            trialEndTime = new Date();
            imgChosen = trialInfo.Test[index];
            res = dltk.copydct(trialInfo); 
            res.trialEndTime = trialEndTime;
            res.btnClickTime = trialEndTime;   // for clarity
            res.imgChosen = imgChosen;
            res.localTrialNumber = that.getCurrentTrialNumber(true);
            res.localTotalTrialNumber = that.getTotalTrialNumber(true);
            res.index = index;

            that._callCallbackFunctions('onClickedTestBtn', res);
        };


        // -- Default callback functions: they will be attached inside ``this.o`` during init().
        // -- These are NOT meant to be called directly
        this._onPreISI1Default = function _onPreISI1Default() {
            that.$elemTest.hide();
            that.$elemSample.show();
            // window.scrollTo(0, 0); // this causes suboptimal performance (forced sync)
        };

        this._onPreDrawResponseDefault = function _onPreDrawResponseDefault() {
            var msg = o.msgTrialProgress;
            var lclNumbers = o.useLocalTrialNumbersForDisplay;
            msg = msg.replace('${CURRENT}', String(that.getCurrentTrialNumber(lclNumbers) + 1));
            msg = msg.replace('${TOTAL}', String(that.getTotalTrialNumber(lclNumbers)));
            that.$elemTrialCounter.html(msg);
            that.$elemTest.show();
            that.$elemSample.hide();
            testing_period = true;   // buttons are now responsive
        };

        this._getContextsWithMatchingShape = function _getContextsWithMatchingShape() {
            // This returns the list of on-screen contexts that has the same shape
            // as that of an element in trialSpec.  This is provided mainly for overriding.
            return [that.ctx_sample_on, that.ctxs_test_on];
        };

        this._getImgFilesForPreloading = function _getImgFilesForPreloading() {
            // This returns an old-style imgFiles equivalent.  This must match the shape of
            // _getContextsWithMatchingShape()
            var imgFiles = [];  // old-style imgFiles equivalent
            var rsrcsTrialSpecs = o.__Experiment__.rsrcsTrialSpecs;
            var l = rsrcsTrialSpecs.length;

            for (var i = 0; i < l; i++) {
                var elem = [];
                elem.push(rsrcsTrialSpecs[i].Sample);
                elem.push(rsrcsTrialSpecs[i].Test);
                imgFiles.push(elem);
            }
            return imgFiles;
        };

        this._onPreloadRsrcsAsyncDefault = function _onPreloadRsrcsAsyncDefault(argdct) {
            // Preload resources.
            // This will be called when the system passes benchmark successfully by the Experiment object.
            // NOTE: This function MUST call argdct.finished() after loading all resources.  Otherwise,
            // the experiment will hang.
            var ctx_sample_on = that.ctx_sample_on;

            // load fixation dot and blank image first...
            dltk.prepareResources(
                [[o.imgFixation, []], [o.imgBlank, []]], [ctx_sample_on, []],
                function() {
                    // ...then load trial images
                    dltk.prepareResources(
                        that._getImgFilesForPreloading(),
                        that._getContextsWithMatchingShape(),
                        argdct.finished,    // MUST call this when successfully proloaded all resources
                        function (progress, total) {
                            var argdct2 = {progress: progress, total: total, msg: ''};
                            var msg = that._getPreloadProgressText(argdct2);
                            dltk._$$$(_$, argdct.elemPreload).html(msg);
                        },
                        {rsrcs: that.rsrcs}
                    );
                },
                null,    // no progress update here
                {rsrcs: that.rsrcs});
            // Note: no need to call zen.preload() anymore
        };

        this._onBeginExpDefault = function _onBeginExpDefault() {
            // Make the sample (answer) canvases clickable (This func is called by the Experiment object)
            var make_handler = function make_handler(idx) {
                return function () {
                    if (testing_period)
                        that._clickedTestBtn(idx);
                };
            };

            for (var i = 0; i < that.$elemTestClickables.length; i++)
                that.$elemTestClickables[i].click(make_handler(i));
        };

        this._onRunNextTrialAsyncDefault = function _onRunNextTrialAsyncDefault (argdct) {
            // This is called by Experiment object to procced to the next trial
            // Since this is an async function, argdct.finished() must be called upon successful
            // completion of rendering of this trial.  This is internally done inside _runTrialOnce()
            that.currentTrialInfo = argdct.trialInfo;
            that._safeRunTrialOnce(argdct);
        };


        // -- Public methods
        this.init = function init() {
            // Initialize various RSVP related stuffs
            var i, rsrcsTrialSpecs;

            // shape must match
            if (o.elemTestCanvasIDs.length != o.elemTestClickables.length) {
                dltk.setDebugMessage('init: "elemTestCanvasIDs" and "elemTestClickables" ' +
                        'have different shapes.');
                return false;
            }

            rsrcsTrialSpecs = o.__Experiment__.rsrcsTrialSpecs;
            for (i = 0; i < rsrcsTrialSpecs.length; i++) {
                if (typeof(rsrcsTrialSpecs[i].Sample) != 'string') {
                    setDebugMessage('init: illegal "Sample" at ' + String(i));
                    return false;
                }
                if (rsrcsTrialSpecs[i].Test.length != o.elemTestCanvasIDs.length) {
                    setDebugMessage('init: illegal "Test" at ' + String(i));
                    return false;
                }
                if (typeof(rsrcsTrialSpecs[i].SampleDuration) != 'number') {
                    setDebugMessage('init: illegal "SampleDuration" at ' + String(i));
                    return false;
                }
                if (typeof(rsrcsTrialSpecs[i].ISI) != 'number') {
                    setDebugMessage('init: illegal "ISI" at ' + String(i));
                    return false;
                }
            }

            // -- ok to go
            that.$elemSample = dltk._$$$(_$, o.elemSample);
            that.$elemTest = dltk._$$$(_$, o.elemTest);
            that.$elemTrialCounter = dltk._$$$(_$, o.elemTrialCounter);
            that.$elemTestClickables = [];
            for (i = 0; i < o.elemTestClickables.length; i++)
                that.$elemTestClickables.push(dltk._$$$(_$, o.elemTestClickables[i]));

            // on screen buffers for double buffering.
            // from: http://blog.bob.sh/2012/12/double-buffering-with-html-5-canvas.html
            that.ctx_sample_on = dltk.getOnScreenContextFromCanvas(o.elemSampleCanvasID);
            for (i = 0; i < o.elemTestCanvasIDs.length; i++)
                that.ctxs_test_on.push(dltk.getOnScreenContextFromCanvas(o.elemTestCanvasIDs[i]));

            // attach all default callback functions properly
            for (var k in o) {
                if (o.hasOwnProperty(k) && typeof(k) == 'string') {
                    if (!k.startsWith('on') || !k.endsWith('Default') || typeof(o[k]) != 'string')
                        continue;
                    if (!callable(that[o[k]])) {
                        dltk.setDebugMessage('init: ambigious reference: ' + o[k]);
                    }
                    o[k] = that[o[k]];
                }
            }

            that.$elemSample.hide();
            that.$elemTest.hide();
            o.optdctQueueTrial.rsrcs = that.rsrcs;
            testing_period = false;

            return true;
        };

        this.getCurrentTrialInfo = function getCurrentTrialInfo() {
            // Returns the current info
            return that.currentTrialInfo;
        };

        this.getCurrentTrialNumber = function getCurrentTrialNumber(getLclNumbers) {
            // Returns the current trial number
            if (getLclNumbers) {
                var h = o.__Experiment__.handle;
                return that.getCurrentTrialInfo().localTrialNumbers[h];
            }
            return that.getCurrentTrialInfo().trialNumber;
        };

        this.getTotalTrialNumber = function getTotalTrialNumber(getLclNumbers) {
            // Returns the total trial number
            if (getLclNumbers)
                return o.__Experiment__.localTotalTrialNumber;
            return o.__Experiment__.globalTotalTrialNumber;
        };
    };  // end of RSVPModule



    // -- RSVP with postmasking
    dltk.RSVPWithPostMaskModule = function RSVPWithPostMaskModule(_$, optdct) {
        /**********************************************************************
         This implements RSVP with post masking.
         See dltk.Experiment and dltk.RSVPModule for other information.
         **********************************************************************/
        dltk.RSVPModule.call(this, _$, optdct);   // inherit RSVPModule

        var OPTDCT_DEFAULT = {
            /*** callback functions: these MUST be short to run (ideally less than 2ms) ***/
            onPreMask: null,
            onPostMask: null,
        };
        var that = this;
        var was_gap = false;   // there was a gap between stim and mask?

        // -- Public variables
        var o = dltk.applyDefaults(this.o, OPTDCT_DEFAULT);   // should be "this.o"  (overrides "o")
        this.o = o;            // Make this public in case for overriding
        this.__optdct__ = o;   // This is required by Experiment

        // -- Methods that form fundamentals of this class.  USERS DO NOT CALL THESE DIRECTLY.
        // -- They are public ONLY in order to make them overridable.
        this._preMask = function _preMask() {
            that._callCallbackFunctionsSyncOnly('onPreMask', that.__argdct_ui__);
        };
        this._postMask = function _postMask() {
            that._callCallbackFunctionsSyncOnly('onPostMask', that.__argdct_ui__);
        };

        var _getRSVPTrialSpecs_super = this._getRSVPTrialSpecs;     // a copy of the super method
        this._getRSVPTrialSpecs = function _getRSVPTrialSpecs(argdct) {
            // Returns a spec for "standard" RSVP tasks (this overrides the super method)
            var trial_specs = _getRSVPTrialSpecs_super(argdct);
            var c = argdct.trialInfo;
            var mask = c.PostMask;
            var maskduration = c.PostMaskDuration;
            var gapduration = defined(c.GapDuration) ? c.GapDuration : 0;

            // insert the post mask
            trial_specs.splice(2, 0, {
                urls: [mask],
                contexts: [that.ctx_sample_on],
                duration: maskduration,
                pre: that._preMask,    // this MUST be short to run
                post: that._postMask   // this MUST be short to run
            });
            // insert the gap if needed
            if (gapduration > 0) {
                trial_specs.splice(2, 0, {
                    urls: [o.imgBlank],
                    contexts: [that.ctx_sample_on],
                    duration: gapduration,
                });
                was_gap = true;
            }
            else
                was_gap = false;

            return trial_specs;
        };

        this._getContextsWithMatchingShape = function _getContextsWithMatchingShape() {
            // (Overriding the super method)
            return [that.ctx_sample_on, that.ctxs_test_on, that.ctx_sample_on];
        };

        this._getImgFilesForPreloading = function _getImgFilesForPreloading() {
            // (Overriding the super method)
            var imgFiles = [];  // old-style imgFiles equivalent
            var rsrcsTrialSpecs = o.__Experiment__.rsrcsTrialSpecs;
            var l = rsrcsTrialSpecs.length;

            for (var i = 0; i < l; i++) {
                var elem = [];
                elem.push(rsrcsTrialSpecs[i].Sample);
                elem.push(rsrcsTrialSpecs[i].Test);
                elem.push(rsrcsTrialSpecs[i].PostMask);
                imgFiles.push(elem);
            }
            return imgFiles;
        };

        var _getTimingAnalysisResults_super = this._getTimingAnalysisResults;   // copy of the super method
        this._getTimingAnalysisResults = function _getTimingAnalysisResults(hist, hist_delta, hist_delta_flush) {
            // (Overriding the super method)
            var diag;
            var res = _getTimingAnalysisResults_super(hist, hist_delta, hist_delta_flush);
            var offset = (was_gap) ? 1 : 0;
            var t_mask = dltk.round2(res.t_spent_all[3 + offset]);
            var t_ISI2 = dltk.round2(res.t_spent_all[4 + offset]);
            var t_gap;
            if (was_gap) {
                t_gap = dltk.round2(res.t_spent_all[3]);
                diag = 'ISI1, stimon, gap, mask, ISI2 = ' + String(res.t_ISI1) + ', ' + String(res.t_stim) +
                    ', ' + String(t_gap) + ', ' + String(t_mask) + ', ' + String(t_ISI2);
            }
            else {
                t_gap = 0;
                diag = 'ISI1, stimon, mask, ISI2 = ' + String(res.t_ISI1) + ', ' + String(res.t_stim) +
                    ', ' + String(t_mask) + ', ' + String(t_ISI2);
            }
            res.t_mask = t_mask;
            res.t_ISI2 = t_ISI2;
            res.t_gap = t_gap;
            res.__diag_msg__ = diag;
            return res;
        };

        // -- Public methods
        var init_super = this.init;   // a copy of the super class' init()
        this.init = function init() {
            // call the super method first, and fail if it fails.
            if (!init_super())
                return false;

            var rsrcsTrialSpecs = o.__Experiment__.rsrcsTrialSpecs;
            for (var i = 0; i < rsrcsTrialSpecs.length; i++) {
                if (typeof(rsrcsTrialSpecs[i].PostMask) != 'string') {
                    setDebugMessage('init: illegal "PostMask" at ' + String(i));
                    return false;
                }
                if (typeof(rsrcsTrialSpecs[i].PostMaskDuration) != 'number') {
                    setDebugMessage('init: illegal "PostMaskDuration" at ' + String(i));
                    return false;
                }
            }
            return true;
        };
    };   // end of RSVPWithPostMaskModule
}(window.dltk = window.dltk || {}, window));
