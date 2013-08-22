__author__ = 'lucy'

from ws4py.websocket import WebSocket
from resources.linkchecker import *

class LinkCheckerSocketHandler( WebSocket ):

    checker = None

    def __init__( self, *args, **kw ):
        WebSocket.__init__( self, *args, **kw )


    ## ------------- handle requests --------------------
    def check( self, data ):
        """
            retrieves the url + recursive depth from the data and launches the
            checking process.
        """
        # gets the url and recursive depth
        data = json.loads( str( data ) )
        print data

        # checks that a checker exists
        if self.checker is None:
            print "no checker..."
            return

        # if the checker is already running, informs the client
        if self.checker.checking:
            print "already checking"
            self.send_msg( "already_checking" )
            return

        # feeds the checker and re-init the canceled flag
        nbr_links = len( self.checker.feedwith( data["url"] ) )
        self.canceled = False

        # sends a "begin" message
        self.checking_output_handler(
            "Found %d potential links... <br />Starting checking<br />"
                                      % ( nbr_links,) )

        # launches the checking process asynchronously
        self.checker.check_async( recursive_depth = data["rec_depth"],
            print_function = self.checking_output_handler,
            callback=self.send_broken_links )

        print "launched checking..."

    def cancel_check( self, arg="" ):
        """
            Cancels the checking process if any
        """
        print "received cancel ", self.checker.checking

        # if the checking is running, stops it and sets the canceled flag to True
        if self.checker is not None and self.checker.checking is True:
            self.checker.stop_checking( )
            self.canceled = True
            print "stopped checking ... "
            self.send_msg('checking_canceled')


    ## -------------- utils -------------------
    def checking_output_handler(self, msg):
        """
            The print function passed to the checker. Sends the output to the client
        """
        if not self.canceled: self.send_msg( 'checking_stream', "%s</br>" % (msg,) )


    def send_broken_links( self ):
        """
            passed as a callback to the check function of the checker,
            sends the results when the checking process is finished (but has not been canceled)
        """
        # be sure that the task was not canceled
        if self.canceled : return

        print len( self.checker.brokenlinks )
        # converts dict to object
        print map( lambda l: l.as_obj(), self.checker.brokenlinks )
        # sends the objects
        self.send_msg('broken_links', {
            'brokenlinks': map( lambda l: l.as_obj(), self.checker.brokenlinks ),
            'nbr_visited': len( self.checker.visited_links )
            })

    ## ---------------- websocket -----------------

    def received_message( self, payload ):
        """
            dispatcher : calls the proper function depending on the event type
        """
        print "received ", type( payload )
        payload = json.loads( str( payload ) )
        # determines which function to call
        callback = getattr( self, payload.get( "type" ) )
        if callback is not None and hasattr( callback, '__call__' ):
            callback( payload.get( 'data' ) )


    def send_msg( self, message_type, message="" ):
        """
            Sends a message to the client. Format : an object with type and data keys.
            The data will be converted to json for the transport.
        """
        self.send( json.dumps( {'type': message_type, 'data': message } ) )
        print "sent ", message_type, " ", message

    def closed( self, code, reason = None ):
        """
            Cancels the checking job if any
        """
        self.cancel_check( )