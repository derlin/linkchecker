#!/usr/bin/env python
# -*- coding: utf-8 -*-
import httplib
import os

__author__ = 'lucy'

class LinkDict( dict ):
    """
        This class holds a dictionary with infos related to links.
        It is made to be used in conjonction with the LinkChecker module.
        required keys : [href|src], tag, code, lineno
        optional keys : full_url, level, page, and all the possible attributes of a html tag
    """

    def get_url( self ):
        """
            returns the url as it was referenced in the tag
        """
        return self.has_key( "href" ) and self[ "href" ] or self[ "src" ]

    def get_absolute_url( self ):
        """
            returns the absolute url.
            In case of anchors or js functions for example, the absolute url may be None.
        """
        if self.has_key( "full_url" ): return self[ "full_url" ]
        return self.get_url()

    def get_status_code( self ):
        """
            returns the http status code
        """
        if not self.has_key( 'code' ): return None
        return "%s (%s)" % (self[ "code" ], httplib.responses[ self[ "code" ] ] )

    def attr_keys( self ):
        """
            returns the keys to the attributes, i.e. everything which is not of first importance
        """
        attrs = [ ]
        for key in sorted( self ):
            if not key in [ 'code', 'href', 'src', 'lineno' ]:
                attrs.append( key )
        print attrs
        return attrs

    def is_broken( self ):
        """
            returns true if the link is suspicious, false otherwise
            (i.e. checks for a status code attribute)
        """
        return self.has_attr( "code" )

    def to_string( self, newline=None ):
        """
            returns the dictionary as string.
            @param:
                newline : the line ending to use.
                    If none, the default system line endings will be used
        """
        if newline is None: newline = os.linesep
        str = " {" + newline

        for key in self.keys( ):
            if key == "code":
                str += "   %-11s => %s%s" % (  key, self.get_status_code( ), newline )

            elif key in [ 'src', 'href' ]:
                str += "   %-11s => %s%s" % ( ( "%s (%s)" % ('url', key) ), self[ key ], newline )

            else:
                str += "   %-11s => %s%s" % ( key, self[ key ], newline ) #.encode('utf8')

        str += " }"

        return str

    def to_html( self ):
        """
            returns a html version of the dictionary
        """
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
        """
           converts the dictionary to an object :
           self.code   => the status code
           self.url    => the url
           self.lineno => the line number
           self.attrs  => all the other stuff, in a dict
        """
        l = {
            'code': self.get_status_code( ),
            'url': self.get_url( ),
            'lineno': "%d, %d" % ( self[ 'lineno' ] ),
            'attrs': {}
        }

        for key in self.attr_keys( ): l[ 'attrs' ][ key ] = self[ key ]
        return l
