"""
Module that holds all information of a session of scrounger

TODO: Make it be used by console modules
"""

from os import popen as _popen

name           = ""

options        = {}
global_options = {}
exceptions     = []

rows, columns  = _popen('stty size', 'r').read().split()
rows, columns  = int(rows), int(columns)