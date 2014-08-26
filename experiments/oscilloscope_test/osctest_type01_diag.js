var numFrames = [];
function installKeyHandler() {
    var nframes = null;
	document.onkeypress = function(e) {  
        var evtobj = window.event? event : e;
        var unicode = evtobj.charCode? evtobj.charCode : evtobj.keyCode;
        var actualKey = String.fromCharCode(unicode);
        if (actualKey >= '0' && actualKey <= '9') {
            // if number entered...
            nframes = parseInt(actualKey, 10);
            $('#_preload').show();
            $('#_preload').html("<font color=black style=background-color:gray>Entry #" + (numFrames.length + 1) + ": " + nframes + " (Press 'w' or 'a' or '.' to commit.  Press 'x' to skip.  Press 'c' to show buffers.)</font>");
        }
        else if (actualKey == 'x') {
            $('#_preload').hide();
            clicked(0);
        }
        else if (actualKey == '.' || actualKey == 'a' || actualKey == 'w') {
            if (nframes === null) {
                $('#_preload').show();
                $('#_preload').html("<font color=black style=background-color:gray>Enter number of frames first.</font>");
            }
            else {
                numFrames.push(nframes);
                pushExpSpecificDiagVariables();
                $('#_preload').hide();
                clicked(0);
            }
        }
        else if (actualKey == 'c') {
            promptDiagVariables();
        }
    };
}

// Handle experiment specific diagnostic varaibles
var l_full_history = [];
var l_full_history_delta = [];
var l_full_history_delta_flush = [];
function pushExpSpecificDiagVariables() {
    l_full_history.push(full_history);
    l_full_history_delta.push(full_history_delta);
    l_full_history_delta_flush.push(full_history_delta_flush);
}

function promptDiagVariables() {
    window.prompt("Copy to clipboard:", JSON.stringify({
        numFrames: numFrames,
        // must include experiment specific variables:
        l_full_history: l_full_history,
        l_full_history_delta: l_full_history_delta,
        l_full_history_delta_flush: l_full_history_delta_flush,
    }));
}


