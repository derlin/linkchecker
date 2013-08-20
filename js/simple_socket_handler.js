/* Ismael Celis 2010
 Simplified WebSocket events dispatcher (no channels, no users)

 var socket = new FancyWebSocket();

 // bind to server events
 socket.bind('some_event', function(data){
 alert(data.name + ' says: ' + data.message)
 });

 // broadcast events to all connected users
 socket.send( 'some_event', {name: 'ismael', message : 'Hello world'} );
 */

var SimpleSocketHandler = function( url )
{
    var conn = new WebSocket( url );
    console.log( conn );
    var callbacks = {};

    this.bind = function( message_type, callback )
    {
        callbacks[ message_type ] = callbacks[ message_type ] || [];
        callbacks[ message_type ].push( callback );
        return this;
    };

    this.send = function( message_type, event_data )
    {
        var payload = JSON.stringify( { type: message_type, data: event_data } );
        conn.send( payload ); // <= send JSON data to socket server
        return this;
    };

    // dispatch to the right handlers
    conn.onmessage = function( evt )
    {
        var json = JSON.parse( evt.data );
        dispatch( json.type, json.data );
    };

    conn.onclose = function()
    {
        dispatch( 'close', null );
    };

    conn.onopen = function()
    {
        dispatch( 'open', null );
    };

    var dispatch = function( message_type, message )
    {
        console.log( "event name " + message_type );
        var chain = callbacks[ message_type ];

        if( typeof chain == 'undefined' ) return; // no callbacks for this event
        for( var i = 0; i < chain.length; i++ ){
            chain[i]( message )
        }
    }
};