var loading = false;
var current_url = null;
$(function(){
    $("#waiting").hide();
    
    $('#clear-container button').button().click( function(){ console.log("clear"); $("#results").html('') } );
    $('#url_textfield').keypress( function( event ) {
        
        if ( event.which != 13 || loading ) return;
          
        if( is_url_valid( $(this).val() )){
            
            console.log( "url valid" );
            $( "#validation" ).hide();
            $( "#waiting" ).show();
            
            loading = true;
            current_url = $( this ).val();
            console.log("ajax");
             
            $.ajax({
                type: "POST",
                url : "/ajax_query",
                data: { url : current_url },
                success : function( result ){
                    loading = false;
                    $("#waiting").hide();
                    console.log( result );
                    handle_result( result );
                    //$("#results").html( result );
                }
            });
         
        }else{
            $( "#validation" ).css('display', 'inline-block');
        }

    });
});

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
    $('.dialog[index=' + i + ']').dialog({ width: 400 });
}

function handle_result_table( data ){
    console.log( data.length );
    
    table = $('<table></table>');
    var excluded = ['code', 'src', 'href'];
    for( var i = 0; i < data.length; i++ ){
        $(table).append( $('<tr><td>url</td><td>' + data[i]['url'] + '</td></tr>') );
        $(table).append( $('<tr class="code"><td>code</td><td>' + data[i]['code'] + '</td></tr>') );
        $(table).append( $('<tr><td>line(s)</td><td>' + data[i]['lineno'] + '</td></tr>') );
        var hidden = $('<tr class="hidden"><td>' + key + '</td><td>' + data[i]['attrs'][key] + '</td></tr>');
        for( var key in data[i]['attrs'] ){
            $(hidden).append( $('<div><span class="key">' + key + '</span><span class="value">' + data[i]['attrs'][key] + '</span></div>') );
        }
        $(table).append( hidden );
    }
    
    $('#results').html(table);
    
}


function waiting(){
    console.log("waiting");
    $("#waiting").text( $("#waiting").text() + "." );
}

function is_url_valid( url ){
    return /^(http|https|ftp):\/\/[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$/i.test( url );
}

