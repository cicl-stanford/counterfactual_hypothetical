/* task.js
 *
 * This file holds the main experiment code.
 *
 * Requires:
 *   config.js
 *   psiturk.j
 *   utils.js
 */

// Create and initialize the experiment configuration object
var $c = new Config(condition, counterbalance);

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc);

// Preload the HTML template pages that we need for the experiment
psiTurk.preloadPages($c.pages);

// Objects to keep track of the current phase and state
var CURRENTVIEW;
var STATE;

/*************************
 * INSTRUCTIONS
 *************************/

var Instructions = function() {
    // Enforce condition for testing
    // $c.condition = 1
    

    $(".slide").hide();
    var slide = $("#instructions-training-1"); 
    slide.fadeIn($c.fade);

    // CURRENTVIEW = new Demographics();
    // CURRENTVIEW = new TestPhase();
    // CURRENTVIEW = new PretrialReminder();
    // CURRENTVIEW = new Comprehension();

    slide.find('.next').click(function () {
        // CURRENTVIEW = new TestPhase();
        // // CURRENTVIEW = new Demographics();
        // CURRENTVIEW = new Demographics();
        CURRENTVIEW = new Comprehension();
    });
};

/*****************
 *  COMPREHENSION CHECK QUESTIONS
 *****************/
 var Comprehension = function() {

    var that = this;

    // Show the slide
    $(".slide").hide();
    $("#comprehension_check").fadeIn($c.fade);

    //disable button initially
    $('#comprehension').prop('disabled', true);

    //checks whether all questions were answered
    $('.demoQ').change(function() {
        if ($('input[name=statement]:checked').length > 0 &&
            $('input[name=block]:checked').length > 0 &&
            $('input[name=judgment]:checked').length > 0) {
            $('#comprehension').prop('disabled', false)
        } else {
            $('#comprehension').prop('disabled', true)
        }
    });

    // upon hitting the 'Continue' button
    $('#comprehension').click(function() {
        var q1 = $('input[name=statement]:checked').val();
        var q2 = $('input[name=block]:checked').val();
        var q3 = $('input[name=judgment]:checked').val();

        // correct answers
        answers = ["C", "C", "D"]

        if (q1 == answers[0] && q2 == answers[1] && q3 == answers[2]) {
            
             // CURRENTVIEW = new TestPhase();
             CURRENTVIEW = new PretrialReminder();
        } else {
            $('input[name=statement]:checked').prop('checked', false);
            $('input[name=block]').prop('checked', false);
            $('input[name=judgment]').prop('checked', false);
            
            CURRENTVIEW = new ComprehensionCheckFail();
        }
    });
}

/*****************
 *  COMPREHENSION FAIL SCREEN*
 *****************/

var ComprehensionCheckFail = function(){
// Show the slide
    $(".slide").hide();
    $("#comprehension_check_fail").fadeIn($c.fade);
    $('#instructions-training-1-button').unbind();
    $('#comprehension').unbind();

    $('#comprehension_fail').click(function () {
      CURRENTVIEW = new Instructions();
      $('#comprehension_fail').unbind();
       });
}


/*********************
 *  PRETRIAL REMINDER  *
 *********************/

var PretrialReminder = function(){
    // Show slides
    $(".slide").hide();
    $("#pretrial_reminder").fadeIn($c.fade);
    $('#instructions-training-1-button').unbind();
    $('#comprehension').unbind();

    $('#reminder_button').click(function () {
      CURRENTVIEW = new TestPhase();
      $('#reminder_button').unbind();
       });
}



/*****************
 *  TRIALS       *
 *****************/

var TestPhase = function () {
    // Initialize relevant TestPhase values
    this.trialinfo;
    this.response;


    var prompt_prep = function(){
         //insert the right image of question statement
            var quest_im = '../static/images/hypothetical_statement.png' 
            var quest_tx = "Ball B would go through the gate if ball A wasn't there. "

            var lab_left = (($c.condition == 0) ? "not at all" : "very much")
            var lab_right = (($c.condition == 0) ? "very much" : "not at all")

            //create the appropriate html
            var quest_html = "<img id=question_img src=" + quest_im + " alt=" + quest_tx +" width='680'>"
            var label_html = "<label style='width: 33%'>" + lab_left + "</label><label style='width: 33%'></label><label style='width: 33%'>" + lab_right +"</label>"

            //add the html to the document
            $('#question').html(quest_html)
            $('#s_label').html(label_html)
    }



    // Define the trial method which runs recursively
    this.run_trial = function () {
        // If we have exhausted all the trials, transition to next phase and close down the function, otherwise run the trial
        if (STATE.index >= $c.trials.length) {
            CURRENTVIEW = new Demographics();
            return
        } else {
            // get the appropriate trial info
            this.trialinfo = $c.trials[STATE.index];

            // update the prgoress bar. Defined in utils.js
            update_progress(STATE.index, $c.trials.length);

            
    // *** material preperation *** //
            prompt_prep();
      
            // initialize parameters
            var video_play_counter = 0;
            var replay_times = 0;
            
            var video_path = "";

           
                
           
            // video setup
            // get the video name and set appropriate video formats for different types of browsers.
            var video_name = this.trialinfo.name;
    
            // pre-load videos 
            $("#part_mp4").attr("src", "/static/videos/part/mp4/" + video_name + '.mp4');
            $("#part_webm").attr("src","/static/videos/part/mp4/" + video_name + '.webm');
            $('.part_video').load();

            $("#full_mp4").attr("src", "/static/videos/full/mp4/" + video_name + '.mp4');
            $("#full_webm").attr("src","/static/videos/full/mp4/" + video_name + '.webm');
            $('.full_video').load();


    // *** run experiments *** //
            // set up event handler for the video reload button
            $("#play.next").click(function () {
                $('.part_video').trigger("play");
                
                video_play_counter++;
                $("#play.next").prop("disabled", true);


                if (video_play_counter == 1) {
                    $("#play.next").html("Watch again");
                    

                } else if (video_play_counter == 2) {
                    $("#play.next").html("Replay");
                    $("#play.next").css('visibility', 'hidden');
                    $('.slider').show();
                    $('#s_label').show();
           
                }
                    else   {  
                    $("#play.next").html("Replay");

                }  
            });



            //set up event handler when video ended
            $(".part_video").on("ended",
                function(){

                if (video_play_counter >= 2) {

                    
                    
                    $("#slider-container").show();
                    $(".guide_text").show();
                    // $('#trial_next').hide();
                
                    $("#play.next").css("visibility", "visible");
                    $("#play.next").prop('disabled', false);

                   
                    $("#feedback.next").show();
                    $("#feedback.next").prop('disabled', true);

                        if ($('.slider').slider("value") == ""){ 
                            $("#feedback.next").prop('disabled', true);
                    }  else {
                            $("#feedback.next").prop('disabled', false);
                    } 

                } else {

                    $("#play.next").prop('disabled', false);

                    }
                });

            // set event handler for Feedback button
            $("#feedback.next").click(function(){
                $('.continue').hide();

                // record video replay times
                replay_times = video_play_counter - 2
                // reset counter
                video_play_counter = 0


                // make slider invisible
                $('.slider').hide();
                $('#s_label').hide();

                 // console report slider value (for debugging)
                 // console.log($('.slider').slider('values'))

            
                // show 'Next trial' button, disabled
                $('#trial_next').show()         
                $('#trial_next').prop('disabled', true);

                $(".guide_text").hide();

                // show the full video
                    // switch video from part to full
                $('.part_video').hide();
                $('.full_video').show();
     
                $('.full_video').trigger("play");
                
                $(".full_video").on("ended", function(){
               // console report slider value (for debugging)
                 
                    $('.continue').hide();
                    $('#trial_next').show();
                    $('#trial_next').prop('disabled', false);
                })

            })
    

            // initialize the slider itself with event handler
            // enable 'Feedback' button once user starts sliding 
            $('.slider').slider().on("slidestart", function(event, ui) {
                // when the slider is "started", show the handle
                $(this).find('.ui-slider-handle').show();
                $("#feedback.next").prop('disabled', false);  
        
            });

    
      
    // *** start of experiment *** //
            
            // hide all displayed html
            $('.slide').hide();

            // show the trial section of the html
            $('#trial').fadeIn($c.fade);

            // set up initial html features 
             $("#slider-container").hide() 
             $(".guide_text").hide()
             $('.full_video').hide()

             //initialize video button names
            $("#play.next").html("Play video")

             $('#trial_next').html('Continue')
             $("#trial_next").hide() 

             $("#feedback.next").html('Full video');
             $("#feedback.next").hide()

            // Slider handle should be initially hidden (until clicked see event handler)
            $('.ui-slider-handle').hide();
            
            // Continue buttons should be initially disabled
             // $('.continue').hide();
            $('#trial_next').prop('disabled', true);
            $("#feedback.next").prop('disabled', true);  

            //show question statement
            $("#prompt-text").show();
            $("#question").show();
            $('.slider').slider('enable')


            // start timer for recording how long people have watched the video
            var start = performance.now();


            //save the tPhase object for use in the event handler
            tPhase = this;
           

            // set the event handler for the next trial button
            $cont_button = $('#trial_next');

            // set the event handler for the continue click
            $cont_button.on('click', function() {

                    //unbind functions 
                    $(".part_video").unbind();
                    $(".full_video").unbind();
                    $("#feedback.next").unbind();
                    
                    // visibilities
                    $('#play.next').prop('disabled', false);
                    $('.continue').show();
                    $('.proceed').show();
                    
                    // data recording
                    var response = $('.slider').slider('value');
                    
                    var response_time = performance.now() - start
                    var data = {
                        'id': tPhase.trialinfo.id,
                        'name': tPhase.trialinfo.name,
                        'gate_pass': tPhase.trialinfo.gate_pass,
                        'response': response,
                        'time': response_time,
                        'replay_times': replay_times
                    }
                    // psiTurk.recordTrialData([tPhase.trialinfo.name, response]);
                    psiTurk.recordTrialData(data);


                    // increment the state
                    STATE.set_index(STATE.index + 1);

                    //disable this event handlers (will be re-assigned in the next trial)
                    $cont_button.off();

                    // reverse the order of video display
                    $('.full_video').hide();
                    $('.part_video').show();

                    $('.slider').slider('option', 'value', "")

                    // disables slider event handler if it exists
                    $('.slider').slider().off("slidestart");

                    // Run the trial again with the new index
                    tPhase.run_trial();
                    return
              });
           
            };
        
    };

    // initialize first trial
    this.run_trial()
};


/*****************
 *  DEMOGRAPHICS*
 *****************/

var Demographics = function(){

    var that = this;

    // Show the slide
    $(".slide").hide();
    $("#demographics").fadeIn($c.fade);

    //disable button initially
    $('#trial_finish').prop('disabled', true)

    //checks whether all questions were answered
    $('.demoQ').change(function () {
      
        var gen_check = $('input[name=gender]:checked').length > 0
        var age_check = $('input[name=age]').val() != "" || $('input[name=age]:checked').length > 0
        var race_check = $('input[name=race]').val() != "" || $('input[name=race]:checked').length > 0
        var eth_check = $('input[name=ethnicity]:checked').length > 0
        if (gen_check && age_check && race_check && eth_check) {
            $('#trial_finish').prop('disabled', false)
        } else {
            $('#trial_finish').prop('disabled', true)
        }
    });

     // for Age: deletes additional values in the number fields
    $('.numberQ').change(function (e) {
        if($(e.target).val() > 100){
            $(e.target).val(100)
        }
    });


     // for Age: make binary options for input field vs checkbox
     // clear input field upon clicking 'Prefer not to say'
     $('#age_na.demoQ').click(function () {
        $('input[name=age]').val("") 
        $('#age_na.demoQ').prop('disabled', false)
    });

     // uncheck 'Prefer not to say' when input field is filled 
    $('input[name=age]').change(function () {
        if($('input[name=age]').val() != ""){
            $('#age_na.demoQ').prop('checked', false)
        } else{
            $('#age_na.demoQ').prop('checked', true)
        }
    });


    // for Race: make binary options for dropdown bar vs checkbox
    // clear dropdown bar upon clicking 'Prefer not to say'
     $('#race_na.demoQ').click(function () {
        $('#race_na.demoQ').prop('disabled', false)
        $('select.demoQ.dropdown').val("NA")   
    });

     // clear dropdown bar upon clicking 'Prefer not to say'
     $('select.demoQ.dropdown').click(function () {
        $('#race_na.demoQ').prop('disabled', false)
        $('#race_na.demoQ').prop('checked', false)
    });

    this.finish = function() {

        // Show a page saying that the HIT is resubmitting, and
        // show the error page again if it times out or error
        var resubmit = function() {
            $(".slide").hide();
            $("#resubmit_slide").fadeIn($c.fade);

            var reprompt = setTimeout(prompt_resubmit, 10000);
            psiTurk.saveData({
                success: function() {
                    clearInterval(reprompt);
                    finish();
                },
                error: prompt_resubmit
            });
        };

        // Prompt them to resubmit the HIT, because it failed the first time
        var prompt_resubmit = function() {
            $("#resubmit_slide").click(resubmit);
            $(".slide").hide();
            $("#submit_error_slide").fadeIn($c.fade);
        };

        // Render a page saying it's submitting
        psiTurk.preloadPages(["submit.html"])
        psiTurk.showPage("submit.html") ;
        psiTurk.saveData({
            success: psiTurk.completeHIT,
            error: prompt_resubmit
        });
    }; //this.finish function end

    $('#trial_finish').click(function () {
       var feedback = $('textarea[name = feedback]').val();
       var gender = $('input[name=gender]:checked').val();
       var age = $('input[name=age]').val();
       var race = $('#race').val();
       var ethnicity = $('input[name=ethnicity]:checked').val();

       psiTurk.recordUnstructuredData('feedback',feedback);
       psiTurk.recordUnstructuredData('gender',gender);
       psiTurk.recordUnstructuredData('age',age);
       psiTurk.recordUnstructuredData('race',race);
       psiTurk.recordUnstructuredData('ethnicity', ethnicity)
       that.finish();
   });
};


// --------------------------------------------------------------------
// --------------------------------------------------------------------

/*******************
 * Run Task
 ******************/

$(document).ready(function() {
    // Load the HTML for the trials
    psiTurk.showPage("trial.html");

    // Record various unstructured data
    psiTurk.recordUnstructuredData("condition", condition);
    psiTurk.recordUnstructuredData("counterbalance", counterbalance);

    // Start the experiment
    STATE = new State();
    // Begin the experiment phase
    if (STATE.instructions) {
        CURRENTVIEW = new Instructions();
        // CURRENTVIEW = new TestPhase()
    } else {
        CURRENTVIEW = new TestPhase();
    }
});
