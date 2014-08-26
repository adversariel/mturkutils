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
            $('#_preload').html("<font color=black style=background-color:gray>Entry #" + (numFrames.length + 1) + ": " + nframes + " (Press 'w' or 'a' or '.' to commit.  Press 'x' to skip.  Press 'c' to show buffers.  Press 'p' to show buffers as a new popup.)</font>");
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
        else if (actualKey == 'p') {
            promptDiagVariables(true);
        }
    };
}

// Handle experiment specific diagnostic varaibles
var lEstmStimPaint = [];
var lEstmStimDur = [];
var lEstmStimErase = [];
var lEstmISI2 = [];
function pushExpSpecificDiagVariables() {
    lEstmStimPaint.push(t0q - t0);
    lEstmStimDur.push(t1q - t0q);
    lEstmStimErase.push(t1q - t1);
    lEstmISI2.push(t2q - t1q);
}

function promptDiagVariables(asPopup) {
    var strout = JSON.stringify({
        numFrames: numFrames,
        // must include experiment specific variables:
        lEstmStimPaint: lEstmStimPaint,
        lEstmStimDur: lEstmStimDur,
        lEstmStimErase: lEstmStimErase,
        lEstmISI2: lEstmISI2,
    });

    if (asPopup === true) {
        var ScreenWidth = window.screen.width;
        var ScreenHeight = window.screen.height;
        var movefromedge = 0;
        var placementx = (ScreenWidth/2)-((400)/2);
        var placementy = (ScreenHeight/2)-((300+50)/2);
        var WinPop = window.open("About:Blank","","width=400,height=300,toolbar=0,location=0,directories=0,status=0,scrollbars=0,menubar=0,resizable=0,left="+placementx+",top="+placementy+",scre enX="+placementx+",screenY="+placementy+",");
        var SayWhat = "<p>" + strout + "</p>";
        WinPop.document.write('<html>\n<head>\n</head>\n<body>'+SayWhat+'</body></html>');
    }
    else window.prompt("Copy to clipboard:", strout);
}


