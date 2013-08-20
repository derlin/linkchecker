__author__ = 'lucy'

# source : http://www.ralph-heinkel.com/blog/category/web/
import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

cherrypy.config.update( {'server.socket_port': 9000} )
WebSocketPlugin( cherrypy.engine ).subscribe( )
cherrypy.tools.websocket = WebSocketTool( )

SUBSCRIBERS = set( )

class Publisher( WebSocket ):
    def __init__(self, *args, **kw):
        WebSocket.__init__( self, *args, **kw )
        print args
        SUBSCRIBERS.add( self )

    def closed(self, code, reason = None):
        SUBSCRIBERS.remove( self )


class Root( object ):
    @cherrypy.expose
    def index(self):
        html = """\
<!DOCTYPE html>
        <html>
        <head>
            <script src="http://code.jquery.com/jquery-1.10.1.min.js"></script>
            <script>
            var websocket = new WebSocket('ws://localhost:9000/ws');
            websocket.onopen    = function (evt) { console.log("Connected to WebSocket server."); };
            websocket.onclose   = function (evt) { console.log("Disconnected"); };
            websocket.onmessage = function (evt) { console.log("received msg"); document
            .getElementById('msg')
            .innerHTML = evt.data; };
            websocket.onerror   = function (evt) { console.log('Error occured: ' + evt.data); };

            function send_hello(){
                $.get("/notify?msg=Hello", function(){ console.log("???");});
            }
            </script>
        </head>
        <body>
            <h1>Websocket demo</h1>
            <button value="hello" onclick="send_hello()"/>
            Message: <span id="msg" />
        </body>
        </html>
"""
        return html

    @cherrypy.expose
    def ws(self):
        """Method must exist to serve as a exposed hook for the websocket"""

    @cherrypy.expose
    def notify(self, msg):
        print msg
        for conn in SUBSCRIBERS:
            conn.send( msg )

cherrypy.quickstart( Root( ), '/', config = {'/ws': {'tools.websocket.on': True,
                                                     'tools.websocket.handler_cls': Publisher}} )