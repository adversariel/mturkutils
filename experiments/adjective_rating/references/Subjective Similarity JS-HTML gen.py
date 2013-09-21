# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

cd objectome_32/

# <codecell>

import itertools
combs = list(itertools.combinations(range(0, 64), 2))

# <codecell>

import cPickle as pk
meta = pk.load(file('meta64_rotonly_graybg.pkl', 'rb'))

# <codecell>

import random
numReps = 30
trials = []
for pair in combs:
    for i in range(0, numReps):
        trial = []
        trial.append('http://s3.amazonaws.com/subjsimilarity/'+random.sample(list(meta[meta['obj'] == models64[pair[0]]]), 1)[0][14]+'.png')
        trial.append('http://s3.amazonaws.com/subjsimilarity/'+random.sample(list(meta[meta['obj'] == models64[pair[1]]]), 1)[0][14]+'.png')
        shuffle(trial)
        trials.append(trial)

# <codecell>

shuffle(trials)

# <codecell>

import json
f = file('/mindhive/dicarlolab/u/esolomon/objectome_32/subj_similarity_js/imgFiles_30reps_pair.js', 'wb')
f.write('var imgFiles = '+json.dumps(trials))
f.close()

# <codecell>

models64 = ['weimaraner',
 'lo_poly_animal_TRTL_B',
 'lo_poly_animal_ELE_AS1',
 'lo_poly_animal_TRANTULA',
 'foreign_cat',
 'lo_poly_animal_CHICKDEE',
 'lo_poly_animal_HRS_ARBN',
 'MB29346',
 'MB31620',
 'MB29874',
 'interior_details_033_2',
 'MB29822',
 'face7',
 'single_pineapple',
 'pumpkin_3',
 'Hanger_02',
 'MB31188',
 'antique_furniture_item_18',
 'MB27346',
 'interior_details_047_1',
 'laptop01',
 'womens_stockings_01M',
 'pear_obj_2',
 'household_aid_29',
 '22_acoustic_guitar',
 'MB30850',
 'MB30798',
 'MB31015',
 'Nurse_pose01',
 'fast_food_23_1',
 'kitchen_equipment_knife2',
 'flarenut_spanner',
 'womens_halterneck_06',
 'dromedary',
 'MB30758',
 'MB30071',
 'leaves16',
 'lo_poly_animal_DUCK',
 '31_african_drums',
 'lo_poly_animal_RHINO_2',
 'lo_poly_animal_ANT_RED',
 'interior_details_103_2',
 'interior_details_103_4',
 'MB27780',
 'MB27585',
 'build51',
 'Colored_shirt_03M',
 'calc01',
 'Doctor_pose02',
 'bullfrog',
 'MB28699',
 'jewelry_29',
 'trousers_03',
 '04_piano',
 'womens_shorts_01M',
 'womens_Skirt_02M',
 'lo_poly_animal_TIGER_B',
 'MB31405',
 'MB30203',
 'zebra',
 'lo_poly_animal_BEAR_BLK',
 'lo_poly_animal_RB_TROUT',
 'interior_details_130_2',
 'Tie_06']

# <codecell>

len(trials)/90

# <codecell>

for num in np.arange(0,len(trials)/90):
    webpage = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Subjective Similarity Rating</title>

<style>
	body { 
		margin:0; 
		padding: 0; 
		font-family: 'trebuchet ms', trebuchet, verdana;
	}

	div,pre { margin:0; padding:0 }

	h2 { margin: 20px 0 5px 0; padding: 0 }

	p.intro { 
		margin: 0; 
		padding: 15px; 
		background: #eee; 
		font-size: small; 
	}

	div#tutorial {
		position:relative; 
		background-color: white;  
		padding: 10px;
	}

	#preview {
		position:absolute;
		border:1px solid #ccc;
		background:#333;
		padding:5px;
		display:none;
		color:#fff;
	}
</style>

<link href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/themes/base/jquery-ui.css" rel="stylesheet" type="text/css"/>
<script type="text/javascript" src="http://code.jquery.com/jquery-1.8.0.min.js"></script>
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/jquery-ui.min.js"></script>
<script type="text/javascript" src="http://web.mit.edu/esolomon/www/browserdetect.js"></script>
<script type="text/javascript" src="http://web.mit.edu/esolomon/www/zen.js"></script>
<script type="text/javascript" src="http://esolomon.scripts.mit.edu/ip.php"></script>
<script type="text/javascript" src="http://web.mit.edu/esolomon/www/javascripts/detect-zoom.js"></script>
<script type="text/javascript" src="http://web.mit.edu/esolomon/www/javascripts/slider.js"></script>

<script type="text/javascript" src="https://s3.amazonaws.com/objectome_html/imgFiles_30reps_pair.js"></script>

<script type="text/javascript">

shuffle = function(o) { 
	for(var j, x, i = o.length; i; j = parseInt(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);
	return o;
};

function gup(name)
{
  name = name.replace(/[\[]/,"\[").replace(/[\]]/,"\]");
  var regexS = "[\?&]"+name+"=([^&#]*)";
  var regex = new RegExp( regexS );
  var param = regex.exec( window.location.href );
  if( param == null )
    return "";
  else
    return param[1];
}

function init_vars() {
	begin = false;
	zoom = DetectZoom.zoom();
	aID = gup("assignmentId");
	response = new Array();
	trialDurations = new Array();
	trialStartTime = new Date();
	StimDone = new Array();
	imgFiles_new = new Array();
	stimduration = 150;
	ISI = 500;
	trialNumber = 0;
	totalTrials = 90;
	startpoint = """+str(num)+""";
	exp_type = "subj_similarity";
	did_famil = false;
}

function familiar() {
	did_famil = true;
	$('#begintask').hide(), $('#_preload').hide(), $('#buttons').hide(), $('#startbuttons').hide();
	$('.test').show(), $('#second_test').hide();
	$('#message').empty();
	var i = 0;
	var f = setInterval(function() {
		console.log(i)
		$('#main_test').attr('src', unlabeled_prototypes[i]);
		i++;
		console.log('New image');
		if (i == unlabeled_prototypes.length) {
			$('#startbuttons p').remove()
			$('#begintask2').hide();
			$('.test').hide();
			
			for (i=0; i < unlabeled_prototypes.length; i++) {
				$('#main').append('<a href="'+unlabeled_prototypes[i]+'" class="preview"><img src="'+unlabeled_prototypes[i]+'" style="float:none; padding:10px; height:100px; width:100px;" /></a>');	
			}
			$('#main').append('<div id="dvi" style="position:absolute; top:5px; left:50%;""><button style="position:relative; left:-50%;" onclick="end_familiarization()">Done Viewing Images</button></div>');
			$.getScript('http://s3.amazonaws.com/objectome_html/subj_similarity_tooltip.js');
			$('.preview').click(function(event) {event.preventDefault();});
			clearInterval(f);
		}
		else {}
	}, 1000)
	return
}

function end_familiarization() {
	$('.preview').remove();
	$('#dvi').remove();
	$('#begintask').unbind('click');
	$('#begintask').show().click(function() {
		beginExp();
	}).html('Begin Experiment');
	$('#startbuttons').show()
	$('#buttons').show();
}

function beginExp() {
	begin = true;
	$('#begintask').hide(), $('#_preload').hide(), $('#buttons').hide(), $('#begintask2').hide();
	$('#startbuttons').empty();
	$('#message').empty();
	$('.fixation').show();
	var stim1 = imgFiles_new[trialNumber][0];
	var stim2 = imgFiles_new[trialNumber][1];
	$('#main_test').attr('src', stim1);
	$('#second_test').attr('src', stim2).hide();
	setTimeout(function() {
		showStim();
	}, ISI);
}

function showStim() {
	$('.test').show();
	$('.fixation').hide();
	setTimeout(function() {
		$('#main_test').hide();  //after stimduration, hide the first image.
		setTimeout( function() {
			$('#second_test').show();  //after ISI, show the second image.
			setTimeout( function() {
				$('.test').hide();  //after stimduration, hide the second image.
				setTimeout( function() {
					showResponse();  //after ISI, show response screen.
				}, ISI);
			}, stimduration);
		}, ISI);
	}, stimduration);
}

function showResponse() {
	sliderRef.f_setValue(50);
	$('#buttons').show();
	trialStartTime = new Date();
	$('#trialCounter').html('Progress: '+trialNumber+' of '+totalTrials);
	if (trialNumber+1 == totalTrials) { }  //Do nothing, skip to submit data func.
	else {
		var stim1 = imgFiles_new[trialNumber+1][0]; //First item in sublist
		var stim2 = imgFiles_new[trialNumber+1][1]; //Second item in sublist.
		$('#main_test').attr('src', stim1);
		$('#second_test').attr('src', stim2);
	}
}

function whitescreen() {
	if (begin) {
		trialEndTime = new Date();
		$('#buttons').hide();
		$('.fixation').show();
		$('#main_test').show();
		$('#second_test').hide();
		rating = parseInt($('#sliderValue').val());
		pushData(rating);
		endTrial();
	}
	else { }
}

function endTrial() {
	if (trialNumber >= totalTrials-1) {
		var resultsobj = [];
		resultsobj.push({
			Response:response,
			ImgOrder:imgFiles_new,
			StimShown:StimDone,
			StimDuration:stimduration,
			RT:trialDurations,
			Condition:exp_type,
			Familiarization:did_famil,
			Zoom:zoom,
			IPaddress:user_IP,
			Browser:BrowserDetect.browser,
			Version:BrowserDetect.version,
			OpSys:BrowserDetect.OS,
			WindowHeight:winH,
			WindowWidth:winW,
			ScreenHeight:vertical,
			ScreenWidth:horizontal
		});	  
	  
		document.getElementById("assignmentId").value = aID;
		document.getElementById("data").value = JSON.stringify(resultsobj);
		document.getElementById("postdata").submit();	//Let's think about making this manual.
	}
	else {
		trialNumber = trialNumber + 1;
		setTimeout( function() {
			showStim();
		}, ISI);
	}
}

function pushData(rating) {
	StimDone.push(imgFiles_new[trialNumber])
	response.push(rating);
	trialDurations.push(trialEndTime - trialStartTime);
}

function preload_resources() {
	imgFiles_new = imgFiles.slice(startpoint*totalTrials, (startpoint+1)*totalTrials);
	shuffle(imgFiles_new);

	unlabeled_prototypes = ['http://s3.amazonaws.com/objectome32_final/nolabels/04_piano_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/22_acoustic_guitar_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/31_african_drums_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/antique_furniture_item_18_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/build51_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/bullfrog_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/calc01_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/Colored_shirt_03M_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/Doctor_pose02_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/dromedary_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/face7_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/fast_food_23_1_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/flarenut_spanner_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/foreign_cat_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/Hanger_02_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/household_aid_29_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/interior_details_033_2_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/interior_details_047_1_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/interior_details_103_2_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/interior_details_103_4_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/interior_details_130_2_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/jewelry_29_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/kitchen_equipment_knife2_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/laptop01_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/leaves16_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_ANT_RED_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_BEAR_BLK_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_CHICKDEE_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_DUCK_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_ELE_AS1_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_HRS_ARBN_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_RB_TROUT_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_RHINO_2_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_TIGER_B_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_TRANTULA_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/lo_poly_animal_TRTL_B_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB27346_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB27585_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB27780_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB28699_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB29346_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB29822_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB29874_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB30071_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB30203_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB30758_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB30798_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB30850_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB31015_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB31188_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB31405_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/MB31620_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/Nurse_pose01_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/pear_obj_2_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/pumpkin_3_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/single_pineapple_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/Tie_06_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/trousers_03_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/weimaraner_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/womens_halterneck_06_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/womens_shorts_01M_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/womens_Skirt_02M_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/womens_stockings_01M_nolabel.png', 'http://s3.amazonaws.com/objectome32_final/nolabels/zebra_nolabel.png']
	shuffle(unlabeled_prototypes);

	stimFiles = imgFiles_new.flatten()
	stimFiles = stimFiles.concat(unlabeled_prototypes);
}

$(document).ready(function() {
	
	$('#tutorial_original').hide(), $('#tutorial2').hide(), $('#tutorial3').hide();

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
		})
	});

	$("#tutorial").html($("#tutorial_original").html());
	$("#tutorial").dialog({height:700,
		width:700,
		position:"center",
		title:"Instructions"
	});
});

</script>


<body bgcolor="#7F7F7F">
	<div id="main" style="height:1000px; width:auto;">
		<div id="startbuttons" align="center" style="position:relative; top:20px;">
			<button id="begintask" value="" style="height:30px; width:auto;">Begin Familiarization</button>
			<p>
				<b>OR, if you already did a HIT in this group...</b>
			</p>
			<button id="begintask2" value="" style="height:30px; width:auto;">Begin Experiment</button>
		</div>
		<div style="position:absolute; top:160px; left:50%">
			<div align="center" id="message" style="position:relative; left:-50%; width:450px;">
				Hello MTurk workers! If you've done my object recognition HITs before, <u><span onclick="$('#tutorial').html($('#tutorial_original').html()); $('#tutorial').dialog({height:700, width:700, position:'center',title:'Instructions'})" style="cursor:pointer;">be sure to read the instructions here carefully</span></u>. This is a *new* HIT with *different* instructions. If you don't read them, you may do the task improperly and your work will be rejected.
			</div>
		</div>
		<div id="_preload" align="center" style="position:fixed; top:0px; left:10px;"></div>
		<div align="center" id="buttons" name="buttons" style="position:relative; top:250px; z-index:3;">
			<p>
			How similar were the two objects on a scale of 0-100? (100 is most similar)
			<br/>
			Please try to use the full 0-100 range during this experiment.
				<table align="center" border=0>
					<tr>
						<td>
							<form id = "sliderspace" style = "visibility:visible;" method ="get">
							<div align="center" style="padding:5px; pointer-events:none;"><input style="visibility:visible;" id="sliderValue" type="Text" size="3" name="sliderValue"></div>
							<script language="JavaScript">
								var A_TPL = {
									'b_vertical' : false,
									'b_watch': true,
									'n_controlWidth': 500,
									'n_controlHeight': 16,
									'n_sliderWidth': 19,
									'n_sliderHeight': 16,
									'n_pathLeft' : 0,
									'n_pathTop' : 0,
									'n_pathLength' : 481,
									's_imgControl': 'http://web.mit.edu/esolomon/www/img/control_gray_500px.gif',
									's_imgSlider': 'http://web.mit.edu/esolomon/www/img/sldr1v_sl_black.gif',
									'n_zIndex': 1 
								}
								var A_INIT = {
									's_form' : 0,
									's_name': 'sliderValue',
									'n_minValue' : 0,
									'n_maxValue' : 100,
									'n_value' : 50,
									'n_step' : 1
								}
								var sliderRef = new slider(A_INIT, A_TPL);
							</script>
							</form>
							<div align="center" style="padding:5px;">
								<button id="nextTrial" onClick="whitescreen()" >Next Trial</button>
							</div>
						</td>
					</tr>
				</table>
			<br/><span id="trialCounter"></span>
		</div>
		<div class="fixation" align="center" style="position:relative; z-index:2; top:225px; left:0px;">
			<img id="fixation_dot" src="http://s3.amazonaws.com/human_training/fixation.png" />
		</div>
		<div class="test" align="center" style="position:relative; z-index:1; top:200px; left:0px;">
			<div style="position:relative; top:0px; left:0px; z-index:1;">
				<img id="main_test" src="" height=360 width=360  border=0/>
			</div>
			<div style="position:relative; top:0px; left:0px; z-index:-1;">
				<img id="second_test" src="" height=360 width=360 border=0/>
			</div>
		</div>
	</div>

<div id="tutorial_link" style="position:fixed; top:0px; right:10px;" onclick="$('#tutorial').html($('#tutorial_original').html()); $('#tutorial').dialog({height:700,							width:700,position:'center',title:'Instructions'})"><u>View Instructions</u></div>
<div id="tutorial" style="position:relative; z-index:-1"></div>
<div id="tutorial_original" style="position:absolute; z-index:-1;">
	<b>Please read these instructions carefully!</b>
	<p>Thank you for your interest! You are contributing to ongoing vision research at the Massachusetts Institute of Technology McGovern Institute for Brain Research.</p>
	<p><font color=red><b>This task will require you to look at images on your computer screen and click to indicate a response for up to about 15 minutes. If you cannot meet these requirements for any reason, or if doing so could cause discomfort or injury to you, do not accept this HIT.</p>
	<p>We encourage you to try a little bit of this  HIT before accepting to ensure it is compatible with your system. If you think the task is working improperly, your computer may be incompatible.</p></font></b>
	<p>We recommend this task for those who are interested in contributing to scientific endeavors. Your answers will help MIT researchers better understand how the brain processes visual information.</p>
	<center><p onclick="$('#tutorial').html($('#tutorial2').html())"><font color=blue><u>Click here to continue reading</u></font></p></center>
</div>
<div id="tutorial2" style="position:absolute; z-index:-1;">
	<ul>
		<li>You will see a series of images, presented in pairs one-after-another, each one for a very brief time. Each image will feature a single object from 64 possibilities. The objects are common things you might see around your house, on TV, in books, or on the Internet.</li>
		<p>
		<li>After you see a pair of images, <b>you must set the slider to indicate how similar you thought the objects in that pair of images were.</b> You should judge their similarity as a whole and <b>only consider visual aspects of the objects</b>, like shape, shade, and texture. We are not interested in the similarities of their names, categories, or functions.</li>
		<p>
		<li>You will set the slider to a position between 0 and 100, with 0 indicating the least similar and 100 indicating the most similar.</li>
		<p>
		<li>For example, if you saw a picture of a car followed by a picture of a boat, you would judge how visually similar a car and a boat are on a scale of 0-100 and set the slider to indicate your decision. When you've made a decision, click the "Next Trial" button below the slider.</li>
		<p>
		<li>Even if you're not 100% sure of what you saw, <u><b>make your best guess.</b></u> Even if the objects do not seem similar, <b>try your best to use the full range of the slider</b>.</li>
		<p>
		<li>When you have worked though all the image pairs, this HIT <b>will submit itself automatically</b>.</li>
	</ul>
	<center><p onclick="$('#tutorial').html($('#tutorial3').html())"><font color=blue><u>Click here to continue reading</u></font></p></center>
</div>
<div id="tutorial3" style="position:absolute; z-index:-1;">
	<ul>
		<li>Before beginning the experiment, we would like to briefly familiarize you with the types of objects you will be seeing. When you click the "Begin Familiarization" button at the top of the screen, you will see an animation for 1 minute showing examples of the objects in this experiment.</li>
		<p>
		<li>After the animation, you will see all the objects laid out on your screen, and you may look through them briefly before clicking "Done Viewing Images."</li>
		<p>
		<li>You <b>*must*</b> do the familiarization the first time you start a HIT in this batch, but on subsequent HITs of the same type you do not need to do the familiarization again. We keep track of whether you did the familiarization step; if you do not do it at least once, you will not be paid.</li>
		<p>
		<li>After the familiarization, click the "Begin Experiment" button at the top of the screen. <b>Be prepared to see the first image -- it happens very fast!</b> In total you will see and rate 90 image pairs.</li>
		<p>
		<li>If you have questions or concerns about this HIT, feel free to contact the requester. You can re-read these instructions at any time by clicking the link in the upper right-hand corner of the screen. Good luck!</li>
	</ul>
	<center><font color=blue><u><p onclick="$('#tutorial').dialog('close')">Click here to close the instructions</p></center></font></u>
</div>

<!-- This is where data gets submitted to MTurk. For some users, this causes a crash, and I'm not sure why. It isn't too common. -->
<form style="visibility:hidden;" id="postdata" action="https://www.mturk.com/mturk/externalSubmit" method="post">
	<input type="text" name="data" id="data" value="">
    <input type="text" name="assignmentId" id="assignmentId" value="">
</form>

</body>
"""
    webName = 'subj_similarity_'+str(num)+'.html'
    f = open('/mindhive/dicarlolab/u/esolomon/objectome_32/HTML/subj_similarity/'+webName, 'wb')
    f.write(webpage)
    f.close()

# <headingcell level=2>

# Run Experiment

# <codecell>

import dldata.mturkutils.mturkutils as mt
reload(mt)

# <codecell>

desc = """**You may complete as many HITs within this group as you like.** Complete an experiment where you observe about 90 image pairs and make judgments about the similarity of objects that you saw. We expect this HIT to take 7-15 minutes or less, though you must finish in under 25 minutes. By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment."""
comm = """Subjective similarity task to complement pspace data from objectome64 imageset. Subjects are asked to rate the similarity of 90 object pairs with a 0-100 slider. Objects are drawn from the objectome64 set and presented on a gray background with only pose variation. 100 is given as 'most similar' and 0 as 'least similar'."""

ssexp = mt.experiment(sandbox=False, keywords=['experiment', 'cognitive', 'psychology', 'neuroscience'], 
                      title='Object Similarities', reward=0.45, duration = 1500,
                      description = desc, comment = comm, collection_name = 'subjective_similarity', 
                      meta = meta)

# <codecell>

hitids = ssexp.createHIT(ssexp.URLs, verbose=True)

# <codecell>

ssexp.updateDBwithHITs(verbose=True)

# <codecell>

workers = ssexp.collection.find({}, {'_id':0, 'WorkerID':1})
len(unique([w['WorkerID'] for w in workers]))

# <codecell>

mt.updateGeoData('subjective_similarity')

# <codecell>

ssexp.collection.count()

# <codecell>

ssexp.collection.find_one()

# <codecell>


