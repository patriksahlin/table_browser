#!/usr/bin/env python

from distutils.core import setup

setup(name='table_browser-patriksahlin',
      version='0.1',
      description='Curses based data table browser',
      author='Patrik Sahlin',
      author_email='psahlin@gmail.com',
      url='https://github.com/patriksahlin/table_browser',
      packages=['table_browser'],
      entry_points = {
          'console_scripts' : [
              'table_browser = table_browser:main'
              ]
          }
     )

