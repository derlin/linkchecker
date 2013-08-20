# -*- coding: utf-8 -*-
__author__ = 'lucy'
# source : https://bitbucket.org/Lawouach/cherrypy-recipes/src/c899e1b914171d3c3d9f3b80bb22f2e9e41992b6/web/websockets/http_traffic/__init__.py
import json
import logging
import os
import random

import cherrypy
from cherrypy.lib import cpstats
from cherrypy.process import plugins

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

base_dir = os.path.abspath( os.path.dirname( __file__ ) )

class MetricsWebSocketHandler( WebSocket ):
    def received_message(self, m):
        pass


class MetricsBroadcaster( plugins.Monitor ):
    def __init__(self, bus):
        plugins.Monitor.__init__( self, bus, callback = self.broadcast, frequency = 0.2 )

    def broadcast(self):
        s = cpstats.extrapolate_statistics( logging.statistics )
        data = [ ]
        for k in s:
            if k.startswith( "CherryPy HTTPServer" ):
                for w in s[ k ][ "Worker Threads" ]:
                    data.append( s[ k ][ "Worker Threads" ][ w ] )
                break

        data = json.dumps( data, sort_keys = True, indent = 4 )
        cherrypy.engine.publish( 'websocket-broadcast', TextMessage( data ) )


class Root( object ):
    @cherrypy.expose
    def index(self):
        return file( os.path.join( base_dir, 'test_websocket_2.html' ) )

    @cherrypy.expose
    def dummy(self):
        return '*' * random.randint( 1, 256 )

    @cherrypy.expose
    def metrics(self):
        cherrypy.log( "Handler created: %s" % repr( cherrypy.request.ws_handler ) )

if __name__ == '__main__':
    root = Root( )
    root.cpstats = cpstats.StatsPage( )

    cherrypy.config.update( {'server.socket_port': 8090,
                             'server.statistics': True,
                             'server.thread_pool': 3} )

    WebSocketPlugin( cherrypy.engine ).subscribe( )
    cherrypy.tools.websocket = WebSocketTool( )

    MetricsBroadcaster( cherrypy.engine ).subscribe( )

    cherrypy.quickstart( root, '/', {
        '/': {
            'tools.cpstats.on': True
        },

        '/metrics': {
            'tools.cpstats.on': False,
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': MetricsWebSocketHandler
        }
    }
    )