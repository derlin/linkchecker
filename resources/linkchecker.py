#!/usr/bin/env python

import re

import requests
from HTMLParser import HTMLParser
import httplib

from threading import Thread
from multiprocessing import JoinableQueue
import multiprocessing

import json


class LinkDict( dict ):
    """
    def __init__( self, *arg, **kw ):
        super( LinkDict, self ).__init__( *arg, **kw )
      
    def __setitem__( self, key, value ):
        print "set" + key
        if key in ['src', 'href']:
            print "changed key"
            key = 'url'
        dict.__setitem__( self, key, value )
    
    def get( self, key ):
        return self.__getitem__( key)
        
    def __getitem__( self, key ):
        print "get" + key
        if key in ['src', 'href']:
            print "changed key"
            key = 'url'
        
        return "lala"
        return dict.__getitem__(self, key)
       
       
    def __repr__(self):
        print "repr"
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        print 'update', args, kwargs
        for k, v in dict(*args, **kwargs).iteritems():
            if k in ['href', 'src']: 
                k = 'url'
                print "changed key"
            self[k] = v
    """
    
    def get_url( self ):
        return self.has_key("href") and self["href"] or self["src"]
        
    def get_status_code( self ):
        if not self.has_key('code'): return None
        return "%s (%s)" % (self["code"], httplib.responses[ self["code"] ] )
       
    def attr_keys( self ):
        attrs = []
        for key in sorted( self ):
            if not key in ['code', 'href', 'src', 'lineno']: 
                attrs.append( key )
        print attrs
        return attrs
        
    def is_broken( self ):
        return self.has_attr( "code" )
    
    
    def dump( self ):
        print " { "
        
        for key in self.keys():
            if key == "code" : 
                print "   %-11s => %s" % (  key, self.get_status_code() )
                
            elif key in ['src', 'href']:
                print "   %-11s => %s" % ( ( "%s (%s)" % ('url', key) ), self[key] )
                
            else:
                print "   %-11s => %s" % ( key, self[key] ) #.encode('utf8')
        
        print " }"
    
    def dump_for_html( self ):
        output = ""
        output += "<div class='link_dump'>"

        for key in self.keys():
            
            if key == "code" : 
                output += "<div class='entry code'><div class='key'>%-11s</div><div class='value'>%s</div></div>" % (  key, self.get_status_code() )
            elif key in ['src', 'href']:
                output += "<div class='entry url'><div class='key'>%s</div><div class='value'>%s</div></div>" % ( ( "%s (%s)" % ('url', key) ), self[key] )
            else:
                output += "<div class='entry'><div class='key'>%s</div><div class='value'>%s</div></div>" % ( key, self[key] ) #.encode('utf8')
                
        output += "</div>"
        
        return output
    
    def as_obj( self ):
        l = {}
        l['code'] = self.get_status_code()
        l['url'] = self.get_url()
        print "type ", type(self['lineno'])
        l['lineno'] =  "%d, %d" % ( self['lineno'] )  
        l['attrs'] = {}
        
        for key in self.attr_keys():
            print key, self[key]
            l['attrs'][key] = self[key]
        return l
    
# create a subclass and override the handler methods
class LinkChecker( HTMLParser ):
    
    def __init__( self, url=None ):
        HTMLParser.__init__( self )
        if url is not None: self.feedwith( url )

        
    ## feeds the checker with a new url
    #@brief 
    # this method triggers the parsing of the page indicated by the <param>url</param link.
    # Afterwards, all the links found in the page are available through self.links. Each link is
    # in a dictionary format, with keys : 'tag' + all the attributes found ... 
    #@param the absolute url to fetch
    def feedwith( self, url ):
        self.base_url = url
        self.links = []
        self.brokenlinks = []
        self.feed( requests.get( url ).text )

     
    #override
    def handle_starttag(self, tag, attrs):
        attrs = dict( attrs )
        
        if 'src' in attrs.keys() or 'href' in attrs.keys():
            l = LinkDict( { 'tag': tag, 'lineno' : self.getpos() } )
            l.update( attrs )
            self.links.append( l )

    ### triggers the check of all the links found in the page.
    #@brief 
    # this method must be called after having fed the checker with a new url.
    # afterwards, all the broken links found will be available in the self.broken_links variable.
    #@param verbose
    #   True by default. If the method comments its actions
    def check( self, verbose=True ):
        
        if not hasattr( self, 'base_url' ):
            raise Exception( 'cannot call check before feeding the checker' )
            
        self._verbose = verbose

        # if they don't already exist, creates and starts the worker threads
        if not hasattr( self, 'workers' ):
            self._resultq = multiprocessing.Queue()
            self._jobq = multiprocessing.JoinableQueue()
            self._workers = []
            
            for i in range( multiprocessing.cpu_count() ):
                 w = ( Thread( target=self.__worker ) )
                 self._workers.append( w )
                 w.daemon = True
                 w.start()
            
        for l in self.links: self._jobq.put( l )
        self._jobq.join()       # block until all tasks are done
    
        
        if self._verbose: 
            print "number of deadlinks in this page : ", self._resultq.qsize()
            
        while not self._resultq.empty(): 
            self.brokenlinks.append( self._resultq.get() );
    

    def __worker( self ):
        while True:
            item = self._jobq.get()
            if item is not None:
                result = self.__parse_link( item )
                if result is not None:
                    self._resultq.put( result )
                self._jobq.task_done()
                
                

    def __parse_link( self, l ):
        base = self.getdomain()

        url = l.get_url()
        burl = url
        
        if re.match("^(http|ftp)", url) is None: 
            url = LinkChecker.resolve_relative_link( url, self.base_url )
            l["full_url"] = url
        
        try:
            answer = requests.get( url )
            if answer.status_code == 200:
                if self._verbose: print "  ", url, " OK"
                return None
            # from here, bad link 
            l["code"] = answer.status_code
            return l
        except requests.exceptions.MissingSchema:
            if self._verbose: print "*****invalid : ", burl, " <-> ", url, "******"

        except requests.exceptions.RequestException, e:
            if self._verbose: print "### unknown error ", burl, " <-> ", url, " ", e
        
        return None


    
    def getdir( self ):
        return self.base_url[:self.base_url.rindex("/")+1]
        
    def getdomain( self ):
        return re.search( "(^.+//[^/]+)", self.base_url ).group( 1 )

    
    def dump_broken_links( self ):
        for link in self.brokenlinks:
            link.dump()


    def brokenlinks_to_json( self ):
        obj = []
        for l in self.brokenlinks:
            obj.append( l.as_obj() ) 
        return json.dumps( obj )
        
    @staticmethod
    def resolve_relative_link( url, base_url ):
        
        # the root domain
        try:
            base = re.search( "(^.+//[^/]+)", base_url ).group( 1 )
        except exceptions.AttributeError:
            raise Exception("base_url does not seem to be a valid url !")
        
        # absolute url, nothing to resolve
        if re.match("^(http|ftp)", url) is not None: 
            return url
        
        # root domain
        elif url == "/": 
            url = base
        
         # javascript, anchors, ... skip
        elif url.startswith("javascript") or url[0] in ["#", "?"]: 
            url = None
            
        # url available through http or https
        elif url.startswith("//"):  
            url = "http:" + url
          
        # relative url
        elif url.startswith("../") or url[:1].isalpha():
            # gets the dir. example : http://domain.org/truc/icon.php => http://domain.org/truc/ 
            if re.match("(^.+//[^/]+)$", base): # the dir is the root domain...
                the_dir = base + "/"
            else:
                the_dir = base_url[:base_url.rindex("/")+1]
            # goes back one dir at a time, depending on the number of ../ found
            for i in range( len( re.findall( "../", url ) ) ): the_dir = the_dir[0:the_dir.rindex("/") + 1]
            # appends everything
            url = the_dir + re.findall("^[\.\./]*(.*)$", url )[0]
         
        # relative url, from the root domain
        elif url.startswith("/"): 
            url = base + url

        return url

