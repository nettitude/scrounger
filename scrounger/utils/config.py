"""
Module with scrounger configurations
"""
# get home directory
from os import getenv

# Logging
import logging as _logging

#_LOGGING_FORMAT = "%(asctime)17s - %(module)8s.%(funcName).10s : %(message)s"
_LOGGING_FORMAT = "%(asctime)17s - %(module)30s : %(message)s"
_LOGGING_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
_formatter = _logging.Formatter(_LOGGING_FORMAT, _LOGGING_TIME_FORMAT)
_handler = _logging.StreamHandler()
_handler.setFormatter(_formatter)

Log = _logging.getLogger("scrounger")
"""
Variable to be used when logging is necessary
"""

Log.addHandler(_handler)
#Log.setLevel(_logging.INFO)
Log.setLevel(_logging.DEBUG)

# Constants
SSH_SESSION_TIMEOUT = 60*5 # 5 minutes
SSH_COMMAND_TIMEOUT = 30 # 30 seconds

_BANNER = """
   _____
  / ____|
 | (___   ___ _ __ ___  _   _ _ __   __ _  ___ _ __
  \___ \ / __| '__/ _ \| | | | '_ \ / _` |/ _ \ '__|
  ____) | (__| | | (_) | |_| | | | | (_| |  __/ |
 |_____/ \___|_|  \___/ \__,_|_| |_|\__, |\___|_|
                                     __/ |
                                    |___/
"""
_VERSION = "0.1.0"
_SCROUNGER_HOME = "{}/.scrounger".format(getenv('HOME'))
_HISTORY_FILE = "{}/history".format(_SCROUNGER_HOME)
_MAX_HISTORY = 1000