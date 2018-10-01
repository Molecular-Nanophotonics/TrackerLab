# -*- coding: utf-8 -*-
"""
Discription:
Author: Martin Fränzl
Data: 21/06/18
"""

import subprocess as sp

check = True

try:
	import nptdms
except ImportError:
	response = input('Install nptdms: [y/n]\n')
	if not response or response[0].lower() != 'y':
        #print('Canceled!')
        check = False
	else:
		print('Trying to Install nptdms...')
		sp('pip install nptdms')

try:
	import pyqtgraph
except ImportError:
    response = input('Install pyqtgraph: [y/n]\n')
    if not response or response[0].lower() != 'y':
        print('Canceled!')
        check = False

	else:
		print('Trying to Install pyqtgraph...')
		sp('pip install pyqtgraph')
  
    
if check:      
    print('All required packages are installed.')
else:
    print('Some of the required packages are not installed.')
