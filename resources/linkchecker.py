#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, sys
import requests
from HTMLParser import HTMLParser
from threading import Thread
from multiprocessing import JoinableQueue, Queue
import multiprocessing
from multiprocessing import Lock
import json
import exceptions
import time

from linkdict import LinkDict





# create a subclass and override the handler methods
class LinkChecker( ):

    link_lock = Lock( )  # for operations on self.visited_links
    print_lock = Lock() # for printing
    checking = False
    verbose = True

    def __init__( self, url = None ):
        self.parser = LinkChecker.__Parser( )
        if url is not None: self.feedwith( url )


    ## feeds the checker with a new url
    #@brief 
    # this method triggers the parsing of the page indicated by the <param>url</param link.
    # Afterwards, all the links found in the page are available through self.links. Each link is
    # in a dictionary format, with keys : 'tag' + all the attributes found ... 
    #@param the absolute url to fetch
    def feedwith( self, url ):
        self.base_url = url
        self.count = 0
        self.root_url = self.getdomain( )
        self.visited_links = [ self.base_url, self.root_url ]
        self.__links = self.parser.feedwith( url )
        self.brokenlinks = [ ]
        return self.__links


    def check_async( self, print_function = None, print_queue= None, recursive_depth = 2,
            callback=None ):

        def launch():
            self.check(print_function, print_queue, recursive_depth)
            if callback is not None: callback()

        Thread(target=launch).start()

    def stop_checking(self):
        self.checking = False
        while not self.__jobq.empty():
            pass

    ### triggers the check of all the links found in the page.
    #@brief 
    # this method must be called after having fed the checker with a new url.
    # afterwards, all the broken links found will be available in the self.broken_links variable.
    #@param verbose
    #   True by default. If the method comments its actions
    def check( self, print_function = None, print_queue= None, recursive_depth = 2 ):
        if not hasattr( self, 'base_url' ):
            raise Exception( 'cannot call check before feeding the checker' )

        self.checking = True
        self.__print_queue = print_queue
        self.__print_function = None
        if hasattr(print_function, '__call__'):
            print "fun set "
            self.__print_function = print_function

        self.recursive_depth = recursive_depth
        # if they don't already exist, creates and starts the worker threads
        if not hasattr( self, 'workers' ):
            self.__resultq = Queue( )
            self.__jobq = JoinableQueue( )
            self._workers = [ ]

            for i in range( multiprocessing.cpu_count( ) ):
                w = ( Thread( target = self.__worker ) )
                self._workers.append( w )
                w.daemon = True
                w.start( )

        for l in self.__links:
            self.__jobq.put( l )

        self.__links = None # frees some memory

        while self.__jobq.qsize( ) > 0:
            time.sleep(1)       # block until all tasks are done

        if self.verbose:
            print "number of deadlinks in this page : ", self.__resultq.qsize( )

        while not self.__resultq.empty( ):
            self.brokenlinks.append( self.__resultq.get( ) )


    def __worker( self ):
        """ The run method for the workers. Takes jobs from the links queue, checks the links
            and puts the broken links into the result queue...
            The workers will be blocked by the multiprocessing queue when the latter is empty.
         """
        while True:
            item = self.__jobq.get( )
            #self.print_out(" qsize : %d %s" % (self.__jobq.qsize(), item))
            if item is not None and self.checking is True:
                result = self.__parse_link( item )
                if result is not None:
                    self.__resultq.put( result )

            self.__jobq.task_done( )


    def __is_visited( self, url ):
        """
            returns true if the url has already been visited, false otherwise.
            This method is thread-safe
        """
        self.link_lock.acquire( )
        val = url in self.visited_links
        self.link_lock.release( )
        return val

    def __add_visited( self, url ):
        """
            adds an url to the visited links list.
            This method is thread-safe.
        """
        self.link_lock.acquire( )
        self.visited_links.append( url )
        self.link_lock.release( )


    def __parse_link( self, l ):
        """
            The actual job done by the workers:
             - resolves the url if it is not an absolute one
             - verifies that the url has not been already visited
             - if the recursive depth is greated than 0 and the url is from the same
               domain as the "base url", parses the page and adds the links found to the queue
             - adds the link object to the brokenlinks if the status code is not 200
        """
        if self.__jobq.qsize( ) % 10 == 0:
            self.print_out("   ** %d ** " % ( self.__jobq.qsize( ), ) )
        self.count += 1

        url = l.get_url( )
        burl = url

        # if not absolute url
        if re.match( "^(http|ftp)", url ) is None:
            # tries to resolve the relative url
            url = LinkChecker.resolve_relative_link( url, self.base_url )
            l[ "full_url" ] = url

        # if already visited
        if self.__is_visited( url ):
            self.print_out( "<><> already visited %s" % ( url, ) )
            return

        if url is None:
            self.print_out( "<><> skipping %s" % ( burl, ) )
            return

        # marks this url as visited
        self.__add_visited( url )

        try:
            # if the page must be parsed as well
            if l[ 'level' ] < self.recursive_depth and self.__is_from_same_domain( url ) and \
                re.match( ".*\.(""png|jpg|pdf|gif|xml)$", url,re.I ) is None:
                self.__check_subpage( url, l[ 'level' ] + 1 )
            # actual check
            answer = requests.get( url )

            if answer.status_code == 200:
                self.print_out( "-> %s OK" % ( url, ) )
                return None
                # from here, bad link
            l[ "code" ] = answer.status_code
            return l
        except requests.exceptions.MissingSchema:
            self.print_out( "***** invalid : %s <-> %s " % ( burl, url ) )

        except requests.exceptions.RequestException, e:
            self.print_out( "#### unknown error (%s) : %s <-> %s" % ( e.message, burl, url )  )

        return None


    def __is_from_same_domain( self, url ):
        """
            returns true if the url is from the same domain as the "base link"
        """
        return url.startswith( self.base_url ) or url.replace( "://www.", "://" ).startswith(
            self.base_url )


    def __check_subpage( self, link, level ):
        """
            creates a new parser and adds the links found in the page to the queue
            Note that we must use a new parser, to avoid concurrency between threads
            (this method can indeed be called by the workers)
        """
        self.print_out( "###### checking subpage : %s at level %d " % ( link, level ) )
        parser = LinkChecker.__Parser( )
        links = parser.feedwith( link, level )
        for l in links:
            if not l.get_url( ) in self.visited_links:
                self.__jobq.put( l )

    def getdir( self ):
        """
            returns the base directory of the "base url", for example:
               base url : http://example.com/dir1/hello => http://example.com/dir1/
            The last slash is included, as well as the protocol
        """
        return self.base_url[ :self.base_url.rindex( "/" ) + 1 ]

    def getdomain( self ):
        """
            returns the domain of the base url, as well as the protocol used, for example:
              base url : http://example.com/dir1/hello => http://example.com
            The last slash is NOT included
        """
        return re.search( "(^.+//[^/]+)", self.base_url ).group( 1 )


    def dump_broken_links( self ):
        """
            dumps to standard output all the broken links found in a readable format
        """
        for link in self.brokenlinks:
            link.dump( )


    def brokenlinks_to_json( self ):
        """
            returns a string in json format encoding all the broken links
        """
        obj = [ ]
        for l in self.brokenlinks:
            obj.append( l.as_obj( ) )
        return json.dumps( obj )


    def print_out(self, msg):
        """
            depending on the options, adds the msg to the queue,
            calls a foreign function or print to stdout.
            (see the check method parameters for more infos)
            This method is thread-safe.
        """
        if self.__print_queue is not None:
            self.__print_queue.put(msg)
            return
        self.print_lock.acquire()
        if self.verbose:
            if self.__print_function is not None:
                self.__print_function(msg)
            else:
                print msg
        self.print_lock.release()


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
        elif url.startswith( "javascript" ) or \
             url.startswith( "mailto" ) or \
             url[ 0 ] in [ "#", "?" ]  or \
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


    class __Parser( HTMLParser ):
        """
            The parser.
        """
        def __init__( self ):
            HTMLParser.__init__( self )


        #override
        def handle_starttag(self, tag, attrs):
            attrs = dict( attrs )

            if 'src' in attrs.keys( ) or 'href' in attrs.keys( ):
                l = LinkDict( {'tag': tag, 'lineno': self.getpos( ),
                               'level': self.level,
                               'page' : self.base_url } )
                l.update( attrs )
                self.links.append( l )

        ## feeds the checker with a new url
        #@brief
        # this method triggers the parsing of the page indicated by the <param>url</param link.
        # Afterwards, all the links found in the page are available through self.links. Each link is
        # in a dictionary format, with keys : 'tag' + all the attributes found ...
        #@param the absolute url to fetch
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


