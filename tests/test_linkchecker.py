#!/usr/bin/python

from resources.linkchecker import *

parser = LinkChecker()
#parser.feedwith("http://perrin-traiteur.ch")

def fun():
    print "finish"

links = parser.feedwith( "http://docs.python-requests.org/" )#"http://perrin-traiteur.ch")
print "found ", len( links ), " links"
parser.check_async(recursive_depth=0,callback=fun)

"""

print "added ", parser.count, " links to queue"
print "visited links ", len( parser.visited_links ), " links "

links = parser.feedwith( "http://docs.python-requests.org/" )#"http://perrin-traiteur.ch")
print "found ", len( links ), " links"
time.sleep(4)
parser.check_async()
parser.stop_checking()
parser.dump_broken_links()

print
print "added ", parser.count, " links to queue"
print "visited links ", len( parser.visited_links ), " links "
print len(parser.brokenlinks)

"""