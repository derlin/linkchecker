#!/usr/bin/env python
import os.path
current_dir = os.path.dirname(os.path.abspath(__file__))

import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from resources.linkchecker_socket_handler import *


WebSocketPlugin( cherrypy.engine ).subscribe( )
cherrypy.tools.websocket = WebSocketTool( )


class LinkCheckerWebApp( object ):
    
    parser = LinkChecker()

    @cherrypy.expose
    def ws( self ):
        """Method must exist to serve as a exposed hook for the websocket"""
        print "ws"
        handler = cherrypy.request.ws_handler
        cherrypy.session['handler'] = handler

        if cherrypy.session.get('checker') is None:
            cherrypy.session['checker'] = LinkChecker()

        cherrypy.session.save()
        handler.checker =  cherrypy.session.get('checker')



    @cherrypy.expose
    def index( self ):
        output = open('html/linkchecker_webapp.html').read()
        print current_dir
        #~ htmlTemplate = Template( file='templates/index.tmpl' )
        #~ htmlTemplate.css_scripts=['static/css/main.css']
        #~ return str(htmlTemplate)

        return output


cherrypy.quickstart( LinkCheckerWebApp(), config = {

    'global' : {
        'server.socket_host': "127.0.0.1",
        'server.socket_port': 14000,
        'tools.staticfile.root': "/home/lucy/git/linkchecker",
        'tools.sessions.on': True,
        'tools.sessions.locking' : 'explicit',
        'checker.on': False
    },

    '/ws': {
        'tools.websocket.on': True ,
        'tools.websocket.handler_cls': LinkCheckerSocketHandler
    },

    ## css
    '/index.css': {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename': "css/linkchecker_webapp.css"
    },
    '/round_loading_animated.css': {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename': "css/round_loading_animated.css"
    },

    ## js
    '/socket_handler.js': {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename': "js/simple_socket_handler.js"
    },

    '/index.js': {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename': "js/linkchecker_webapp.js"
    },

    '/scrollTo.js': {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename': "js/jquery.scrollTo-1.4.3.1-min.js"
    }
})
