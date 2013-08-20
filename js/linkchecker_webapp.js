var loading = false;
var current_url = null;
var checking_dialog = null;
var checking_dialog_inner = null;

var MessageTypes = {
    // responses from the server
    IN_CHECKING_STREAM: "checking_stream",
    IN_BROKEN_LINKS: "broken_links",
    IN_CHECKING_CANCELED: "checking_canceled",

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
    server.bind( MessageTypes.IN_CHECKING_STREAM, function( data ){
        $( checking_dialog_inner ).append( data );
        $( checking_dialog ).scrollTo( 'max' );
    });

    server.bind( MessageTypes.IN_BROKEN_LINKS, function( result ){
        loading = false;
        $("#waiting").hide();
        $( checking_dialog_inner ).append(
            $("<br /><div><strong>Finished !</strong> Found " + result.length + " suspicious links...</div>")
        );
        $( checking_dialog ).scrollTo( 'max' );
        console.log( result );
        handle_result( result );
    });

    server.bind( MessageTypes.IN_CHECKING_CANCELED, function( data ){
        console.log( data );
        loading = false;
        $( "#waiting" ).hide();
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
    $( "#clear-container button" ).button();

    $('#clear-button').click( function(){
        console.log("clear");
        $("#results").html('')
    });
    $('#show-console-button').click( function(){
        open_checking_dialog()
    });

    // handles the input field
    $('#url_textfield').keypress( function( event ) {
        
        if ( event.which != 13 || loading ) return;
          
        if( is_url_valid( $( this ).val() )){
            
            console.log( "url valid" );
            $( "#validation" ).hide();
            $( "#waiting" ).show();
            
            loading = true;
            current_url = $( this ).val();

            server.send( MessageTypes.OUT_CHECK, current_url );

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
function handle_result( data ){
    
    $('#results').append( $('<div class="intro">We found <strong>' + data.length + '</strong> suspicious link ' + ( data.length > 1 ? 's' : '' ) + 
        ' on page:<br />' + current_url + '</div>') );
        
    for( var i = 0; i < data.length; i++ ){
        var alink = $('<div class="link" index="' + i + '"></div>');
        alink.append( $('<div class="entry url"><div class="key">url</div><div class="value">' + data[i]['url'] + '</div></div>') )
             .append( $('<div class="entry code"><div class="key">code</div><div class="value">' + data[i]['code'] + '</div></div>') )
             .append( $('<div class="entry lineno"><div class="key">line, col</div><div class="value">' + data[i]['lineno'] + '</div></div>') )
             .append( $('<div class="link-details"><button class="ui-corner-all" onclick="show_details(' + i + ')">details</button></div>') )
        var attrs = $('<div class="dialog ui-corner-all" index="' + i + '" title="Details"></div>');
        for( var key in data[i]['attrs'] ){
            attrs.append( $('<div class="entry"><div class="key">' + key + '</div><div class="value">' + data[i]['attrs'][key] + '</div></div>') );
        }
        alink.append( attrs );
        $('#results').append(alink);
        $('#results button').button();
    }
    
    
}

function show_details( i ){
    $('.dialog[index=' + i + ']').dialog( { width: 400 } );
}

function is_url_valid( url ){
    return /^(http|https|ftp):\/\/[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$/i.test( url );
}

