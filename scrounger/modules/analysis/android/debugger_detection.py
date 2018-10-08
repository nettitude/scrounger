from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.general import pretty_grep, pretty_grep_to_str
from scrounger.utils.android import JDB, forward, remove_forward, smali_dirs

from scrounger.modules.misc.android.make_debuggable import Module as DModule

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
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
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
        {
            "name": "repackage",
            "description": "if set to true recompiles the application with \
debuggable set to true (likely to fail)",
            "required": True,
            "default": False
        },
        {
            "name": "ignore",
            "description": "paths to ignore, seperated by ;",
            "required": False,
            "default": "/com/google/;/android/support/"
        }
    ]

    debug_regex = r"android/os/Debug;->isDebuggerConnected|\
android/content/pm/ApplicationInfo;->flags"

    def run(self):
        result = {
            "title": "Application Does Not Detect Debuggers",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Looking for evidence in smali code")
        debug_evidence = {}
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            debug_evidence.update(pretty_grep(self.debug_regex, smali))

        if debug_evidence:
            result.update({
                "title": "Application Destects Debuggers",
                "report": True,
                "details": "The following evidence was found in the smali \
code:\n{}".format(pretty_grep_to_str(debug_evidence, self.decompiled_apk,
                    ignore))
                })
        else:
            result.update({
                "details": "No evidence of debug detection was found in the \
smali code.",
                "report": True
            })

        if self.repackage:
            Log.info("Trying to modify the application to be debuggable")

            # make the application debuggable
            debug_module = DModule()
            debug_module.decompiled_apk = self.decompiled_apk
            debug_module.device = self.device
            debug_module.output = None # will default to /tmp
            debug_module.install = True
            debug_module.run()

        Log.info("Starting the application and identifying the process ID")
        self.device.start(self.identifier)
        pid = self.device.pid(self.identifier)

        if pid:
            Log.info("Forwarding local ports")
            forward(54321, pid)

            Log.info("Starting JDB")
            jdb = JDB("127.0.0.1", 54321)

            if not jdb.running():
                result.update({
                    "report": True,
                    "details": "{}\n\nScrounger was unable to attach a debugger\
 to the application.".format(result["details"])
                })
            else:
                result.update({
                    "report": True,
                    "details": "{}\n\nScrounger was able to attach a debugger \
to the application:\n\n{}".format(result["details"], jdb.read())
                    }
                )

            Log.info("Removing forwarded ports and exiting jdb")
            remove_forward()
            jdb.exit()

        else:
            Log.error("The application is not running")

        return {
            "{}_result".format(self.name()): result
        }

