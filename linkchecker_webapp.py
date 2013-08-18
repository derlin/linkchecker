#!/usr/bin/env python
import os.path
current_dir = os.path.dirname(os.path.abspath(__file__))

import cherrypy, sys
from resources.linkchecker import *
from cgi import escape
import simplejson as json

class LinkCheckerWebApp( object ):
    
    parser = LinkChecker()
        
    @cherrypy.expose
    def ajax_query( self, url ):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        output = ''

        if url:
            try:
                self.parser.feedwith( url )
                self.parser.check( verbose=False)
                #~ output += '<div>Found ' + str( len( self.parser.brokenlinks ) ) + 'problematic links</div>'
                #~ output += '<div class="links_container">'
                #~ for l in self.parser.brokenlinks:
                    #~ output += l.dump_for_html()
                output = self.parser.brokenlinks_to_json()
            except Exception, e:
                print e
                #~ output += "<div class='error'> Error: " + str(e) + " " + url
                #~ output += '</div>'
            
            
        return output

    @cherrypy.expose
    def index( self ):
        output = open('html/linkchecker_webapp.html').read()
        print current_dir
        #~ htmlTemplate = Template( file='templates/index.tmpl' )
        #~ htmlTemplate.css_scripts=['static/css/main.css']
        #~ return str(htmlTemplate)

        return output

cherrypy.quickstart( LinkCheckerWebApp(), config="linkchecker_webapp.conf" )
