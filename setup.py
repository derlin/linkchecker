#from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name = 'linkchecker',
    version = '1.0',
    packages = [ 'resources' ],
    install_requires = [ 'cherrypy', 'ws4py', 'cherrypy-wsgiserver' ],
    url = '',
    license = '',
    author = 'lucy',
    author_email = 'lucy.derlin@gmail.com',
    description = 'simple webapp offering tools to find broken links on web pages'
)
