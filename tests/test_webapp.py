#!/usr/bin/env python
# -*- coding: utf-8 -*-

# source : http://tools.cherrypy.org/wiki/Comet
# string.Template requires Python 2.4+
from string import Template
from resources.linkchecker import *

import cherrypy

__author__ = 'Lucy Linder'
# Thanks to joshthecoder for the pid-in-session bit

# Trying to cut down on long lines...
jquery_url = 'http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js'
jquery_ui_url = 'http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js'
jquery_ui_css_url =\
'http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/themes/black-tie/jquery-ui.css'

class Comet(object):


    """An example of using CherryPy for Comet-style asynchronous communication"""
    @cherrypy.expose
    def index(self):
        """Return a basic HTML page with a ping form, a kill form, and an iframe"""
        # Note: Dollar signs in string.Template are escaped by using two ($$)
        html = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
  <head>
    <link rel="stylesheet" type="text/css" href="${jquery_ui_css_url}" media="screen" />
    <script type="text/javascript" src="${jquery_url}"></script>
    <script type="text/javascript" src="${jquery_ui_url}"></script>
    <style>
    .fg-button {
    outline: 0;
    clear: left;
    margin:0 4px 0 0;
    padding: .1em .5em;
    text-decoration:none !important;
    cursor:pointer;
    position: relative;
    text-align: center;
    zoom: 1;
    }
    .fg-button .ui-icon {
    position: absolute;
    top: 50%;
    margin-top: -8px;
    left: 50%;
    margin-left: -8px;
    }
    a.fg-button { float:left;  }
    .terminal {
    position: relative;
    top: 0;
    left: 0;
    display: block;
    font-family: monospace;
    white-space: pre;
    width: 100%; height: 30em;
    border: none;
    }
    </style>
  </head>
  <body>
  <script type="text/javascript">
    $$(function(){
        $$('#result').hide();
        $$('#kill_ping').click(function() {
            $$.ajax({
                url: "/kill_proc",
                cache: false,
                success: function(html){
                    window.frames[0].stop();
                    $$("#result").html(html);
                    $$("#result").fadeIn(300);
                }
            });
            return false;
        });
    });
    </script>
  <h3>CherryPy Comet Example</h3>
  <form id="ping_form" target="console_iframe" method="post" action="/ping">
  <input type="text" id="host" name="host" size="18" />
  <button id="ping" class="fg-button ui-state-default ui-corner-all" type="submit">
  Ping
  </button>
  </form>
  <form id="kill_form" method="post" action="/kill_proc">
  <button id="kill_ping" class="fg-button ui-state-default ui-corner-all"
  title="Click to stop to the ping (sends SIGINT)" type="submit">
  Control-C
  </button>
  </form>
  <div id="result" class="ui-state-highlight">
  <span class="ui-icon ui-icon-check ui-icon-left" style="margin-right: .3em;">
  </span>
  </div>
  <iframe name="console_iframe" class="terminal" />
  </body>
</html>
"""
        t = Template(html)
        page = t.substitute(
            jquery_ui_css_url=jquery_ui_css_url,
            jquery_url=jquery_url,
            jquery_ui_url=jquery_ui_url)
        return page




    @cherrypy.expose
    def ping(self, host, **kw):
        """Execute, 'ping <host>' and stream the output"""
        # This javascript just scrolls the iframe to the bottom

        if not cherrypy.session.get('checker'):
            cherrypy.session['checker'] = LinkChecker()
            cherrypy.session.save()

        checker = cherrypy.session.get('checker')

        checker.feedwith( host )


        def run_command():
            q = multiprocessing.Queue()
            yield "begin"
            checker.check_async(print_queue=q)
            yield '<style>body {font-family: monospace;}</style>'

            time.sleep(0.8)
            while checker.checking or not q.empty():
                print " qsize ", q.qsize()
                msg = q.get()
                if not checker.checking:
                    continue
                scroll_to_bottom = '<script type="text/javascript">window.scrollBy(0,50);</script>'
                # The yeilds here are the key to keeping things streaming
                msg += "\n<br />%s" % scroll_to_bottom # include the iframe scroll fix
                yield msg  # Stream it to the browser

            yield "end"

        return run_command()

    @cherrypy.expose
    def kill_proc(self, **kw):
        """Kill the process associated with the pid in our session."""
        checker = cherrypy.session.get('checker')
        print "kill ", checker.checking
        if not checker or not checker.checking:
            return "No active process to kill"
            # Without SIGINT we don't get the final summary from the ping command
        # ...it emulates control-C (SIGKILL or SIGTERM would just end the process with no summary)
        checker.stop_checking()
        return "<strong>Success:</strong> The ping process was killed successfully."
    # Enable streaming for the ping method.  Without this it won't work.


    ping._cp_config = {'response.stream': True}



cherrypy.config.update({
    'log.screen':True,
    'tools.sessions.on': True,
    'tools.sessions.locking' : 'explicit',
    'checker.on':False
})
cherrypy.tree.mount(Comet(), config=None)
cherrypy.engine.start()
#cherrypy.engine.block()