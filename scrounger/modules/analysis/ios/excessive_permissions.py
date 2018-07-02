from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.local.app.entitlements import Module as EModule
from scrounger.utils.ios import plist
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application uses excessive permissions",
        "certainty": 90
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's binary",
            "required": True,
            "default": None
        },
        {
            "name": "info",
            "description": "path to a local Info.plist file",
            "required": True,
            "default": None
        },
        {
            "name": "excessive_permissions",
            "description": "permissions considered excessive, seperated by |",
            "required": True,
            "default": "NSAppleMusicUsageDescription|NSBluetooth|\
NSCalendarsUsage|NSCameraUsage|NSContactsUsage|NSHealthShareUsage|\
NSHealthUpdateUsage|NSHomeKitUsage|NSLocation|NSMicrophone|NSMotionUsage|\
NSPhotoLibraryUsage|NSRemindersUsage|NSLocationAlwaysUsageDescription"
        }
    ]

    def run(self):
        result = {
            "title": "Application Uses Excessive Permissions",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        ent_module = EModule()
        ent_module.binary = self.binary
        ent_result, entitlements = ent_module.run(), None
        for key in ent_result:
            if key.endswith("_entitlements"):
                entitlements = ent_result[key]

        if not entitlements:
            return {"print": "Couldn't get entitlements from binary."}

        Log.info("Analysing Entitlements")
        permissions = []
        if 'get-tasks-allow' in entitlements:
            permissions += ['get-tasks-allow']

        Log.info("Analysing Info.plist")
        info_content = plist(self.info)
        permissions += [
            permission for permission in self.excessive_permissions.split("|")
            if permission in info_content
        ]

        if permissions:
            result.update({
                "report": True,
                "details": "The following permissions were found: * {}".format(
                    "\n* ".join(sorted(permissions)))
            })

        return {
            "{}_result".format(self.name()): result
        }

