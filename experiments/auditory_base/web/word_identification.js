var currentFile = 0;
var soundFiles = ['test1.mp3','test2.mp3','test3.mp3']; // need to load using S3; staged for now
var headphoneFiles = ['antiphase_HC_IOS.wav','antiphase_HC_ISO.wav','antiphase_HC_OIS.wav','antiphase_HC_OSI.wav','antiphase_HC_SIO.wav','antiphase_HC_SOI.wav'];
var headphoneAnswers = [2,3,1,1,3,2];
var headphoneIndex = 0;
var headphoneSucceeded = 0;
var responses = [];
var play_html5_audio = false;

$(document).ready(function() {

	$('#tutorial_original').hide(); $('#tutorial_headphones').hide(); $('#tutorial_ambient').hide();
	$('#buttons').hide();
	$('#begintask2').hide();
	$('#finished').hide();
	$('#headphonecheck').hide();
	$('#headphonefailed').hide();
	$('#ambientcheck').hide();
	$("#tutorial").html($("#tutorial_original").html());
	$("#tutorial").dialog({height:400,
		width:700,
		position: ['middle', 100],
		dialogClass: 'ui-tutorial',
		beforeClose: function(){$('#begintask2').show();}
	});
	if(html5_audio()){
		play_html5_audio = true;
	}
	$(function() {
    $('#userWord').keypress(function (e) {
        if ((e.which && e.which == 13) || (e.keyCode && e.keyCode == 13)) {
            next_trial();
            return false;
        } else {
            return true;
        }
    });
	$('#userWord').autocomplete({
		source: words,
		position: { my : "right bottom", at: "right top" }
	});
});
});

function html5_audio() {
    var a = document.createElement('audio');
    return !!(a.canPlayType && a.canPlayType('audio/mpeg;').replace(/no/, ''));
};

function play_sound(url) {
    var snd, sound;
    if (play_html5_audio) {
		snd = new Audio(url);
		snd.load();
		snd.onended = sound_done;
		return snd.play();
    } else {
		$("#sound").remove();
		sound = $("<embed id='sound' type='audio/mpeg' />");
		sound.attr('src', url);
		sound.attr('loop', false);
		sound.attr('hidden', true);
		sound.attr('autostart', true);
		sound.attr('onended',sound_done());
		return $('body').append(sound);
	}
};

function tutorial_click() {
    $('#tutorial').html($('#tutorial_original').html());
    $("#tutorial").dialog({height:400,
		width:700,
		position: ['middle', 100],
		dialogClass: 'ui-tutorial',
		beforeClose: function(){$('#begintask2').show();}
	});
};

function continue_click(page) {
    $('#tutorial').html($(page).html());
};

function tutorial_close() {
	$('#tutorial').dialog('close');
	$('#begintask2').show();
};

function begin_exp(){
	$('#begintask2').hide();
	$('#headphone1').hide();
	$('#headphone2').hide();
	$('#headphone3').hide();
	$('#headphonecheck').show();
	
};

function headphones(){
	play_sound('resources/'+headphoneFiles[headphoneIndex]);
	$('#headphone1').show();
	$('#headphone2').show();
	$('#headphone3').show();
};

function headphonesresult(result){
	$('#headphone1').hide();
	$('#headphone2').hide();
	$('#headphone3').hide();
	if(result==headphoneAnswers[headphoneIndex++]){
		headphoneSucceeded++;
	}	
	if(headphoneIndex>=5){
		if(headphoneSucceeded>=4){
			$('#headphonecheck').hide();		
			$('#buttons').show();
			listen();		
		}
		else{
			$('#headphonefailed').show();
		}
	}
};


function listen(){
	$('#userWord').autocomplete("close");
	$('#userResponse').hide();
	$('#playingImg').show();
	var soundFile = 'resources/'+soundFiles[currentFile]; // Temporary
	play_sound(soundFile);
}

function sound_done(){
	$('#userResponse').show();
	$('#playingImg').hide();	
	$('#userWord').focus();
};

function next_trial(){
	var wordResponse = $('#userWord')[0].value.toLowerCase();
	if(words.indexOf(wordResponse)==-1){
		return;
	}
	responses.push(wordResponse);
	$('#userWord')[0].value = '';
	if(++currentFile>=soundFiles.length){
		console.log("Done");
		$('#buttons').hide();
		$('#tutorial_link').hide();
		$('#finished').show();
		$('#results')[0].textContent = responses.toString();
		return;
	}
	listen();
};
