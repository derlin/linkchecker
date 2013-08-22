#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'lucy'
## date : august 2013

import re, time
import requests, json
from threading import Thread
import multiprocessing
from multiprocessing import JoinableQueue, Queue, Lock
from linkparser import LinkParser

# create a subclass and override the handler methods
class LinkChecker( ):
    link_lock = Lock( )  # for operations on self.visited_links
    print_lock = Lock( ) # for printing
    checking = False
    verbose = True

    def __init__( self, url = None ):
        self.parser = LinkParser( )
        if url is not None: self.feedwith( url )


    def feedwith( self, url ):
        """
            feeds the checker with a new url
            this method triggers the parsing of the page indicated by the <param>url</param link.
            Afterwards, all the links found in the page are available through self.links. Each link is
            in a dictionary format, with keys : 'tag' + all the attributes found ...
            @param
              url : the absolute url of the page to parse
        """
        self.base_url = url
        self.count = 0
        self.root_url = self.getdomain( )
        self.visited_links = [ self.base_url, self.root_url ]
        self.__links = self.parser.feedwith( url )
        self.brokenlinks = [ ]
        return self.__links


    def check_async( self, print_function = None, print_queue = None, recursive_depth = 0,
            callback = None ):
        """
            launches the checking process of all the links found in the page fed with,
            asynchronously.
            afterwards, all the broken links found will be available in the self.broken_links variable.
            Note that this method MUST be called after feedwith.
            @params:
                print_function: the function to call for output (must take one string argument).
                    Makes sense only if the verbose variable is set to True.
                print_queue: the output strings will be added to this queue instead of being
                    printed (to stdout or through the print_function given)
                    Makes sense only if the verbose variable is set to True.
                recursive_depth: if more than 0 (the default), the pages from
                    the same directory of the base url found during the checking process will be
                    parsed as well.
                    Careful : if the domain is too large, the risk is great that the checking
                        will be endless. Don't try a recursive_depth of 1 with stackoverflow !!

        """

        def launch():
            self.check( print_function, print_queue, recursive_depth )
            self.checking = False
            if callback is not None: callback( )

        Thread( target = launch ).start( )

    def stop_checking(self):
        """
            stops the checking process, if it is running
        """
        self.checking = False
        while not self.__jobq.empty( ):
            pass

    def check( self, print_function = None, print_queue = None, recursive_depth = 2 ):
        """
            launches the checking process of all the links found in the page fed with,
            asynchronously.
            afterwards, all the broken links found will be available in the self.broken_links variable.
            Note that this method MUST be called after feedwith.
            @params:
                print_function: the function to call for output (must take one string argument).
                    Makes sense only if the verbose variable is set to True.
                print_queue: the output strings will be added to this queue instead of being
                    printed (to stdout or through the print_function given)
                    Makes sense only if the verbose variable is set to True.
                recursive_depth: if more than 0 (the default), the pages from
                    the same directory of the base url found during the checking process will be
                    parsed as well.
                    Careful : if the domain is too large, the risk is great that the checking
                        will be endless. Don't try a recursive_depth of 1 with stackoverflow !!

        """
        if not hasattr( self, 'base_url' ):
            raise Exception( 'cannot call check before feeding the checker' )

        self.checking = True
        # handles the parameters
        self.__print_queue = print_queue
        self.__print_function = None
        if hasattr( print_function, '__call__' ):
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

        # puts the jobs in the queue
        for l in self.__links:
            self.__jobq.put( l )

        self.__links = None # frees some memory

        # waits until all tasks are done
        while self.__jobq.qsize( ) > 0:
            time.sleep( 1 )

        if self.verbose:
            print "number of deadlinks in this page : ", self.__resultq.qsize( )

        # transfers the results into the brokenlinks variable
        while not self.__resultq.empty( ):
            self.brokenlinks.append( self.__resultq.get( ) )

        self.checking = False


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
             - verifies that the url has not been already visited
             - if the recursive depth is greated than 0 and the url is from the same
               domain as the "base url", parses the page and adds the links found to the queue
             - adds the link object to the brokenlinks if the status code is not 200
        """
        if self.__jobq.qsize( ) % 10 == 0:
            self.print_out( "   ** %d ** " % ( self.__jobq.qsize( ), ) )
        self.count += 1

        url = l.get_absolute_url( )

        # if already visited
        if self.__is_visited( url ):
            self.print_out( "<><> already visited %s" % ( url, ) )
            return

        # if the url could not be resolved or is not valid
        if url is None:
            self.print_out( "<><> skipping %s" % ( url, ) )
            return

        # marks this url as visited
        self.__add_visited( url )

        try:
            # if the page must be parsed as well
            if l[ 'level' ] < self.recursive_depth and self.__is_from_same_domain( url ) and\
               re.match( ".*\.(""png|jpg|pdf|gif|xml)$", url, re.I ) is None:
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
            self.print_out( "***** invalid : %s <-> %s " % ( l.get_url( ), url ) )

        except requests.exceptions.RequestException, e:
            self.print_out( "#### unknown error (%s) : %s <-> %s" %
                            ( e.message, l.get_url( ), url ) )

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
        parser = LinkParser( )
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


    def brokenlinks_to_string( self, newline = None ):
        """
            returns a string made of all the broken links found in a readable format
            @param:
                newline : the line ending to use.
                    If none, the default system line endings will be used
        """
        output = ""
        for link in self.brokenlinks: output = + link.to_string( )
        return output

    def brokenlinks_to_json( self ):
        """
            returns a string in json format encoding all the broken links
        """
        obj = [ ]
        for l in self.brokenlinks:
            obj.append( l.as_obj( ) )
        return json.dumps( obj )


    def print_out( self, msg ):
        """
            depending on the options, adds the msg to the queue,
            calls a foreign function or print to stdout.
            (see the check method parameters for more infos)
            This method is thread-safe.
        """
        if self.__print_queue is not None:
            self.__print_queue.put( msg )
            return

        self.print_lock.acquire( )
        if self.verbose:
            if self.__print_function is not None:
                self.__print_function( msg )
            else:
                print msg
        self.print_lock.release( )







