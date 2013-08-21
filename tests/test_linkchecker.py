#!/usr/bin/python

from resources.linkchecker import *

parser = LinkChecker()
#parser.feedwith("http://perrin-traiteur.ch")


class Test:

    def lala(self, i, queue, stop):
        while not stop:
            item = queue.get()
            print i, " : ", item
            time.sleep(10 + i)


    def workers(self):

        q = multiprocessing.Queue()
        for i in range(29):
            q.put( " lala %d" % (i,) )

        self.stop = multiprocessing.Value( 'i', False)
        print self.stop
        for i in range(4):
            p = multiprocessing.Process(target=self.lala, args=(i, q, self.stop))
            p.start()
            print i, " started"

test = Test()
test.workers()
time.sleep(3)
print "toujours vivant"
time.sleep(1)
test.stop = True
print "toujours vivant"
time.sleep(10)
print "toujours vivant"
time.sleep(1)
print "toujours vivant"

exit()


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