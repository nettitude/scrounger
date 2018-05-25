from scrounger.core.module import BaseModule

# helper functions / modules
from scrounger.modules.misc.android.app.manifest import Module as ManifestModule
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application requires dangerous \
permissions",
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
            "name": "permissions",
            "description": "dangerous permissions to check for, seperated by ;",
            "required": True,
            "default": "android.permission.GET_TASKS;\
android.permission.BIND_DEVICE_ADMIN;android.permission.USE_CREDENTIALS;\
com.android.browser.permission.READ_HISTORY_BOOKMARKS;\
android.permission.PROCESS_OUTGOING_CALLS;android.permission.READ_LOGS;\
android.permission.READ_SMS;android.permission.READ_CALL_LOG;\
android.permission.RECORD_AUDIO;android.permission.MANAGE_ACCOUNTS;\
android.permission.RECEIVE_SMS;android.permission.RECEIVE_MMS;\
android.permission.WRITE_CONTACTS;android.permission.DISABLE_KEYGUARD;\
android.permission.WRITE_SETTINGS;android.permission.WRITE_SOCIAL_STREAM;\
android.permission.WAKE_LOCK"
        }
    ]

    def run(self):
        result = {
            "title": "The Application Has Inadequate Permissions",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        # create manifest
        manifest_module = ManifestModule()
        manifest_module.decompiled_apk = self.decompiled_apk
        self.manifest = manifest_module.run()
        if "print" in self.manifest:
            return {"print": "Could not get the manifest"}

        self.manifest = self.manifest.popitem()[1]

        Log.info("Analysing application's manifest permissions")

        # setup vars
        permissions = [permission.strip()
            for permission in self.permissions.split(";")]
        app_permissions = self.manifest.permissions()

        inadequate_permissions = []
        for permission in app_permissions:
            if permission in self.permissions:
                inadequate_permissions.append(permission)

        if inadequate_permissions:
            result.update({
                "report": True,
                "details": "* {}".format("\n* ".join(inadequate_permissions))
            })

            return {
                "{}_result".format(self.name()): result,
                "{}_permissions".format(
                    self.manifest.package()): app_permissions
            }

        return {
            "{}_result".format(self.name()): result
        }

