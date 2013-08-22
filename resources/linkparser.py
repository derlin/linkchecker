#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'lucy'
## date : august 2013

import requests, re
from HTMLParser import HTMLParser
from linkdict import LinkDict


class LinkParser( HTMLParser ):
    """
        The links parser.
    """

    def __init__( self ):
        HTMLParser.__init__( self )

    #override
    def handle_starttag( self, tag, attrs ):
        attrs = dict( attrs )

        if 'src' in attrs.keys( ) or 'href' in attrs.keys( ):
            l = LinkDict( {'tag': tag, 'lineno': self.getpos( ),
                           'level': self.level,
                           'page' : self.base_url } )
            l.update( attrs )

            # if not absolute url (must be done here in order to have the proper base_url)
            if re.match( "^(http|ftp)", l.get_url() ) is None:
                # tries to resolve the relative url
                l[ "full_url" ] = LinkParser.resolve_relative_link( l.get_url(),
                    self.base_url )
            self.links.append( l )


    def feedwith( self, url, level = 0 ):
        """
            parses a page, creates a LinkDict object for each href or src found and returns a
             list of LinkDict.
             @params :
                level: the level of the base link (just an attribute added to the LinkDicts
                objects to keep track of the pages when recursion is enabled)
        """
        self.links = [ ]
        self.base_url = url
        self.level = level
        self.feed( requests.get( url ).text )
        return self.links


    @staticmethod
    def resolve_relative_link( url, base_url ):
        """
            transforms a relative link to an absolute one.
            @params:
              url : the url to transform
              base_url : the full and absolute url where the relative link was found
        """
        # the root domain
        try:
            base = re.search( "(^.+//[^/]+)", base_url ).group( 1 )
        except exceptions.AttributeError:
            raise Exception( "base_url does not seem to be a valid url !" )

        # absolute url, nothing to resolve
        if re.match( "^(http|ftp)", url ) is not None:
            return url

        # root domain
        elif url == "/":
            url = base

        # javascript, anchors, ... skip
        elif url.startswith( "javascript" ) or\
             url.startswith( "mailto" ) or\
             url[ 0 ] in [ "#", "?" ]  or\
             re.match( ".*#[^/]+$", url ) is not None :
            url = None

        # url available through http or https
        elif url.startswith( "//" ):
            url = "http:" + url

        # relative url
        elif url.startswith( "../" ) or url[ :1 ].isalpha( ):
            # gets the dir. example : http://domain.org/truc/icon.php => http://domain.org/truc/
            if re.match( "(^.+//[^/]+)$", base ): # the dir is the root domain...
                the_dir = base + "/"
            else:
                the_dir = base_url[ :base_url.rindex( "/" ) + 1 ]
                # goes back one dir at a time, depending on the number of ../ found
            for i in range( len( re.findall( "../", url ) ) ): the_dir = the_dir[ 0:the_dir.rindex(
                "/" ) + 1 ]
            # appends everything
            url = the_dir + re.findall( "^[\.\./]*(.*)$", url )[ 0 ]

        # relative url, from the root domain
        elif url.startswith( "/" ):
            url = base + url

        return url
