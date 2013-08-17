#!/usr/bin/env python

import re

import requests
from linkchecker import *
import json

#~ print "found ", len( re.findall(r'<(([a-z]+)(?:[^>])+(?:href|src)=[\'"]?([^\'" >]+)[^>]*)', requests.get("https://groups.google.com/forum/#!topic/Google-Maps-API/J4uM5LFg2cM").text, re.I ) ), " links with regex"
#~ exit()
# instantiate the parser and feeds it some HTML
#parser = LinkChecker("https://groups.google.com/forum/#!topic/Google-Maps-API/J4uM5LFg2cM")



parser = LinkChecker()
parser.feedwith("http://perrin-traiteur.ch")


print "found ", len( parser.links ), " links with html parser"
#~ for l in parser.links:
    #~ url = l.has_key("href") and l["href"] or l["src"]
    #~ print url, " <=> \n       ", LinkChecker.resolve_relative_link( url, parser.base_url)
    #~ print
#~ 
#~ print LinkChecker.resolve_relative_link( "test.t", parser.base_url)


#~ for t in re.findall(r'<(([a-z]+)(?:[^>])+(?:href|src)=[\'"]?([^\'" >]+)[^>]*)', page.text, re.I ):
    #~ print t
    #~ print
print 

parser.check()
print parser.brokenlinks
print parser.brokenlinks_to_json()

exit()

brokenlinks = []

for link in parser.links:
    result = LinkChecker.__parse_link( parser, link )
    if result is not None:
        brokenlinks.append( result )
  
print "found ", len( brokenlinks ), " broken links"




