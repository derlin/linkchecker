__author__ = 'lucy'

from ws4py.websocket import WebSocket
from resources.linkchecker import *

class LinkCheckerSocketHandler( WebSocket ):

    checker = None

    def __init__( self, *args, **kw ):
        WebSocket.__init__( self, *args, **kw )



    ## ------------- handle requests --------------------
    def check( self, data ):
        data = json.loads( str( data ) )
        print data
        if self.checker is None:
            print "no checker..."
            return

        if self.checker.checking:
            print "already checking"
            self.send_msg( "already_checking" )
            return

        nbr_links = len( self.checker.feedwith( data["url"] ) )
        self.checking_output_handler( "Found %d links... <br />Starting checking<br />" % (nbr_links,) )
        self.checker.check_async( recursive_depth = data["rec_depth"],
            print_function = self.checking_output_handler,
            callback=self.send_broken_links )
        print "launched checking..."

    def cancel_check( self, arg="" ):
        if self.checker is not None and self.checker.checking:
            self.checker.stop_checking( )
            print "stopped checking ... "
        self.send_msg('checking_canceled')


    ## -------------- utils -------------------
    def checking_output_handler(self, msg):
        self.send_msg( 'checking_stream', "%s</br>" % (msg,) )

    def send_broken_links( self ):
        print len( self.checker.brokenlinks )
        time.sleep(2)
        print map( lambda l: l.as_obj(), self.checker.brokenlinks )
        self.send_msg('broken_links', map( lambda l: l.as_obj(), self.checker.brokenlinks ) )

    ## ---------------- websocket -----------------
    def received_message( self, payload ):
        """ dispatcher : calls the proper function depending on the event type """
        print "received ", type( payload )
        payload = json.loads( str( payload ) )

        callback = getattr( self, payload.get( "type" ) )
        if callback is not None and hasattr( callback, '__call__' ):
            callback( payload.get( 'data' ) )


    def send_msg( self, message_type, message="" ):
        self.send( json.dumps( {'type': message_type, 'data': message } ) )
        print "sent ", message_type, " ", message

    def closed( self, code, reason = None ):
        self.cancel_check( )