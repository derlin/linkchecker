#!/usr/bin/env python
# -*- coding: utf-8 -*-
import httplib

__author__ = 'lucy'

class LinkDict( dict ):

    def get_url( self ):
        return self.has_key( "href" ) and self[ "href" ] or self[ "src" ]

    def get_status_code( self ):
        if not self.has_key( 'code' ): return None
        return "%s (%s)" % (self[ "code" ], httplib.responses[ self[ "code" ] ] )

    def attr_keys( self ):
        attrs = [ ]
        for key in sorted( self ):
            if not key in [ 'code', 'href', 'src', 'lineno' ]:
                attrs.append( key )
        print attrs
        return attrs

    def is_broken( self ):
        return self.has_attr( "code" )

    def dump( self ):
        print " { "

        for key in self.keys( ):
            if key == "code":
                print "   %-11s => %s" % (  key, self.get_status_code( ) )

            elif key in [ 'src', 'href' ]:
                print "   %-11s => %s" % ( ( "%s (%s)" % ('url', key) ), self[ key ] )

            else:
                print "   %-11s => %s" % ( key, self[ key ] ) #.encode('utf8')

        print " }"

    def dump_for_html( self ):
        output = ""
        output += "<div class='link_dump'>"

        for key in self.keys( ):
            if key == "code":
                output += "<div class='entry code'><div class='key'>%-11s</div><div class='value'>%s</div></div>" % (
                    key, self.get_status_code( ) )
            elif key in [ 'src', 'href' ]:
                output += "<div class='entry url'><div class='key'>%s</div><div class='value'>%s</div></div>" % (
                    ( "%s (%s)" % ('url', key) ), self[ key ] )
            else:
                output += "<div class='entry'><div class='key'>%s</div><div class='value'>%s</div></div>" % (
                    key, self[ key ] ) #.encode('utf8')

        output += "</div>"

        return output

    def as_obj( self ):
        l = {'code': self.get_status_code( ), 'url': self.get_url( )}
        print "type ", type( self[ 'lineno' ] )
        l[ 'lineno' ] = "%d, %d" % ( self[ 'lineno' ] )
        l[ 'attrs' ] = {}

        for key in self.attr_keys( ):
            print key, self[ key ]
            l[ 'attrs' ][ key ] = self[ key ]
        return l
