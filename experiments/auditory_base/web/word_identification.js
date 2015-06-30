var currentFile = 0;
var soundFiles = ['test1.mp3','test2.mp3','test3.mp3'];
var responses = [];
var play_html5_audio = false;



$(document).ready(function() {

	$('#tutorial_original').hide(); $('#tutorial2').hide(); $('#tutorial3').hide();

	$('.test').hide();
	$('.fixation').hide();
	init_vars();
	preload_resources();
	preload(stimFiles, function(){
		$('#begintask').click(function() {
			familiar();
		});
		$('#begintask2').click(function() {
			beginExp();
		});
	});

	$("#tutorial").html($("#tutorial_original").html());
	$("#tutorial").dialog({height:700,
		width:700,
		position: ['middle', 20], //"center", hahong: no center to hide all buttons
		dialogClass: 'ui-tutorial'
	});

	$('#sl0base').click(function(e) {
		var offset = $(this).offset();
		var pos_x = e.pageX - offset.left;
		console.log(100*pos_x/500);
		sliderRef.f_setValue(100*pos_x/500);
		$('#sl0slider').show();
	});
});

function tutorial_click() {
    $('#tutorial').html($('#tutorial_original').html());
    $('#tutorial').dialog({height:700,width:700,position:['middle', 20],title:'Instructions'});
}

function continue_click(page) {
    $('#tutorial').html($(page).html());
}

function tutorial_close() {
	$('#tutorial').dialog('close');
}