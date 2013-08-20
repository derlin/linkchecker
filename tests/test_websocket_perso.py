__author__ = 'lucy'

# source : http://www.ralph-heinkel.com/blog/category/web/
import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from resources.linkchecker  import *

cherrypy.config.update( {'server.socket_port': 9000} )
WebSocketPlugin( cherrypy.engine ).subscribe( )
cherrypy.tools.websocket = WebSocketTool( )

counter = 0

class Publisher( WebSocket ):
    checker = None

    def __init__(self, *args, **kw):
        WebSocket.__init__( self, *args, **kw )
        global counter
        self.id = counter

    def check(self, url):
        if self.checker is None:
            print "no checker..."
            return

        nbr_links =  len( self.checker.feedwith( url ) )
        self.stream_check( "found %d links... <br />Starting check" % (nbr_links,) )
        self.checker.check_async(print_function=self.stream_check)
        print "launched checking..."

    def cancel_check(self, arg ):
        if self.checker is not None and self.checker.checking:
            self.checker.stop_checking()
            print "stopped checking ... "

    def received_message( self, payload ):

        print "received ", type( payload )
        payload = json.loads( str( payload ) )
        print payload
        fun = getattr( self, payload.get("event") )
        if fun is not None and hasattr( fun , '__call__'):
            fun( payload.get('data') )


    def stream_check(self, msg):
        self.send( json.dumps( {'event': 'checking_stream', 'data': "%s</br>" % (msg,) } ) )
        print "sent ", msg

    def closed( self, code, reason = None ):
       self.cancel_check()



class Root( object ):
    c = 0
    @cherrypy.expose
    def index(self):
        html = """\
<!DOCTYPE html>
        <html>
        <head>
            <script src="http://code.jquery.com/jquery-1.10.1.min.js"></script>
            <script src="/fancy-websocket" type="text/javascript"></script>
            <script>
            var server = new MyFancyWebSocket('ws://localhost:9000/ws');
            server.bind('checking_stream', function(data){ $('#msg').append(data); });


            function appendMsg( data ){
                console.log( data );
                console.log( data.data );
            }
            function send_hello(){
                server.send( 'check', "http://dytherapie.ch" );
                console.log('check send');
            }
            </script>
        </head>
        <body>
            <h1>Websocket demo</h1>
            <button onclick="server.send( 'check', 'http://dytherapie.ch' )">check</button>
            <button onclick="server.send( 'cancel_check', '' )">cancel</button>
            <div id="msg"></div>
        </body>
        </html>
"""

        global counter
        self.id = counter
        counter += 1
        print self.id

        if cherrypy.session.get('id') is not None :
            cherrypy.session['id'] = self.id
            print "setting id"
            cherrypy.session.save()
        return html

    @cherrypy.expose
    def ws(self):
        """Method must exist to serve as a exposed hook for the websocket"""
        handler = cherrypy.request.ws_handler
        cherrypy.session['handler'] = handler

        if cherrypy.session.get('checker') is None:
            cherrypy.session['checker'] = LinkChecker()

        cherrypy.session.save()
        handler.checker =  cherrypy.session.get('checker')

        if cherrypy.session.get('id'):
            print cherrypy.session['id']

    @cherrypy.expose
    def notify(self, msg):

        if cherrypy.session.get('id') is not None:
            print "self id ", cherrypy.session['id']

        handler = cherrypy.session.get('handler')
        if handler is not None:
            handler.check( msg )
            self.c += 1
            print "handler id ", handler.id
            #handler.send( msg )

#        for conn in SUBSCRIBERS:
#            print conn.id
#            if conn.id == self.id + 1 : conn.send( msg )

cherrypy.quickstart( Root( ), '/', config = {

    'global' : {
        'tools.staticfile.root': "/home/lucy/git/linkchecker",
        'tools.sessions.on': True,
        'tools.sessions.locking' : 'explicit',
        'checker.on': False
    },

    '/ws': {
        'tools.websocket.on': True ,
        'tools.websocket.handler_cls': Publisher},

    '/fancy-websocket': {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename': "js/simple_socket_handler.js"
    }
})