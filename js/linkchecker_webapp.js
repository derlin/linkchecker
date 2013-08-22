var loading = false, connected = false;
var current_url = null;
var checking_dialog = null;
var checking_dialog_inner = null;

var nbr_of_searches = 0;

var MessageTypes = {
    // responses from the server
    IN_CHECKING_STREAM: "checking_stream",
    IN_BROKEN_LINKS: "broken_links",
    IN_CHECKING_CANCELED: "checking_canceled",
    IN_ALREADY_CHECKING: "already_checking",
    // requests from the client
    OUT_CHECK: "check",
    OUT_CANCEL_CHECK: "cancel_check"
};


/* *****************************************************************
 * on load
 * ****************************************************************/

 $( function(){

    // ----------- websocket handling -------------
    var server = new SimpleSocketHandler('ws://localhost:14000/ws');
    connected = true;
    server.bind( MessageTypes.IN_CHECKING_STREAM, function( data ){
        append_to_console( data );
    });

    server.bind( MessageTypes.IN_BROKEN_LINKS, function( result ){
        loading = false;
        $("#waiting").hide();
        append_to_console(
            $("<br /><div><strong>Finished !</strong> Found " + result['brokenlinks'].length +
                " suspicious links out of " + result['nbr_visited'] + " ...</div>")
        );
        $( checking_dialog ).scrollTo( 'max' );
        console.log( result );
        handle_result( result );
        nbr_of_searches += 1;
    });

    server.bind( MessageTypes.IN_CHECKING_CANCELED, function( data ){
        console.log( data );
        loading = false;
        $( "#waiting" ).hide();
        append_to_console( $('<div><strong>Checking canceled</strong></div>') );
    });

    server.bind( MessageTypes.IN_ALREADY_CHECKING, function( data ){
        loading = false;
        $( "#waiting" ).hide();
        append_to_console( $('<span>Oops,<br />It seems like you have already launched a process from another window.<br />' +
            'Please, close the other one or wait until the job is finished and try again !</span>') );
    });

    server.bind( 'close', function( data ){
        loading = false;
        $( "#waiting" ).hide();
        connected = false;
        $("#validation .text" ).text("Socket closed" );
        $("#validation").css("display", "inline-block");
        var msg = $('<span>Oops,<br />It seems like the socket has been closed !<br />' +
            'You can maybe try to refresh the page ?</span>');
        append_to_console( msg );
        $("#results" ).append( msg );
    });

    //--------------- init interface -----------------------
    // hides the waiting anim
    $("#waiting").hide();

    // inits the terminal dialog
    checking_dialog = $("#checking_dialog" );
     $( checking_dialog ).dialog({
        autoOpen: false,
        modal: true,
        height: ( $ (window ).height() * 0.6 ),
        width:  ( $( window ).width() * 0.8 ),
        buttons: {
            "Stop task": function(){
                server.send( MessageTypes.OUT_CANCEL_CHECK, "" );

            },
            "Clear": function(){ $( this ).find( ".inner" ).html("") },
            "Close" : function(){
                $( this ).dialog('close');
            }
        }
    });
    checking_dialog_inner = $( checking_dialog ).find(".inner");

    // init clear and show console buttons
    $( "#buttons-container button" ).button();

    $('#clear-button').click( function(){
        console.log("clear");
        $("#results").html('')
    });
    $('#show-console-button').click( function(){
        open_checking_dialog()
    });


    // handles the input field
    $('#url_textfield').keypress( function( event ) {
        
        if ( event.which != 13 || loading || !connected ) return;
          
        if( is_url_valid( $( this ).val() )){
            
            console.log( "url valid" );
            $( "#validation" ).hide();
            $( "#waiting" ).show();
            
            loading = true;
            current_url = $( this ).val();

            server.send(
                MessageTypes.OUT_CHECK,
                JSON.stringify({
                    url: current_url,
                    rec_depth: parseInt($('#rec_select' ).val())
                })
            );

            // opens the dialog
            open_checking_dialog();

        }else{
            $( "#validation" ).css('display', 'inline-block');
        }
    });
});


/* *****************************************************************
 * functions
 * ****************************************************************/

 function open_checking_dialog(){
    if( !$( checking_dialog ).dialog( 'isOpen' ) ){
        $( checking_dialog ).dialog( 'open' );
    }
}
function handle_result( result ){
    var nbr_visited = result['result.nbr_visited'];
    var data = result['brokenlinks'];
    $('#results').append( $('<div class="intro">We found <strong>' + data.length + '</strong> suspicious link ' + ( data.length > 1 ? 's' : '' ) + 
        ' on page:<br />' + current_url + '</div>') );
        
    for( var i = 0; i < data.length; i++ ){
        var alink = $('<div class="link" index="' + i + '"></div>');
        alink.append( $('<div class="entry url"><div class="key">url</div><div class="value">' + data[i]['url'] + '</div></div>') )
             .append( $('<div class="entry code"><div class="key">code</div><div class="value">' + data[i]['code'] + '</div></div>') )
             .append( $('<div class="entry lineno"><div class="key">line, col</div><div class="value">' + data[i]['lineno'] + '</div></div>') )
             .append( $('<div class="link-details"><button class="ui-corner-all" onclick="show_details(\'' + (nbr_of_searches + "_" + i) + '\')">details</button></div>') )
        var attrs = $('<div class="dialog ui-corner-all" id="' + (nbr_of_searches + "_" + i) + '" title="Details"></div>');
        for( var key in data[i]['attrs'] ){
            attrs.append( $('<div class="entry"><div class="key">' + key + '</div><div class="value">' + data[i]['attrs'][key] + '</div></div>') );
        }
        alink.append( attrs );
        $('#results').append(alink);
        $('#results button').button();
    }
    
}

function show_details( id ){
    $('#' + id ).dialog( { width: 400 } );
}

function is_url_valid( url ){
    return /^(http|https|ftp):\/\/[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$/i.test( url );
}

function append_to_console( msg ){
    $( checking_dialog_inner ).append( msg );
    $( checking_dialog ).scrollTo( 'max' );
}