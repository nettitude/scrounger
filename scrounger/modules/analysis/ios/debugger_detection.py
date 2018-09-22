from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.general import strings
from scrounger.utils.ios import GDB

from time import sleep
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application detects debuggers",
        "certainty": 75
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        },
        {
            "name": "identifier",
            "description": "the application's identifier",
            "required": True,
            "default": None
        },
        {
            "name": "device",
            "description": "the remote device",
            "required": True,
            "default": None
        },
    ]

    _regex = r"ptrace"

    def run(self):
        result = {
            "title": "Application Does Not Detect Debuggers",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        Log.info("Getting binary strings")
        strs = strings(self.binary)

        Log.info("Analysing Strings")
        if not re.search(self._regex, strs):
            result.update({
                "report": True,
                "details": "No evidence of the application trying to detect \
debuggers being attached."
            })

        Log.info("Starting the application and identifying the process ID")
        openned, attempts = self.device.start(self.identifier), 0
        while "device locked" in openned[1] and attempts < 3:
            Log.error("Device is locked - cannot open the application")
            Log.info("Please unlock the device - waiting 10 seconds")
            sleep(10)
            openned, attempts = self.device.start(self.identifier), attempts + 1

        pid = self.device.pid(self.identifier)

        if pid:
            Log.info("Starting GDB on the remote device")
            gdb = GDB(self.device)

            Log.info("Attaching GDB to the application")
            gdb_result, attempt = gdb.execute("attach {}".format(pid)), 0

            # try to get stdout, might take time to flush
            while not gdb_result and attempt < 3:
                sleep(5)
                gdb_result, attempt = gdb.read(), attempt + 1

            if gdb_result and "unable to attach" in gdb_result.lower():
                result.update({
                    "title": "Application Detected Debugger Attached",
                    "report": True,
                    "details": "Scrounger was unable to attach a debugger to \
the application."
                })
            elif gdb_result:
                result.update({
                    "report": True,
                    "details": "{}\n\nScrounger was able to attach a debugger \
to the application:\n\n{}".format(result["details"], gdb_result)
                    }
                )

            gdb.exit()

        else:
            Log.error("The application is not running")

        return {
            "{}_result".format(self.name()): result
        }

