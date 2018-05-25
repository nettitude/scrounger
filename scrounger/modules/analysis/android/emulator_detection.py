from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep, pretty_grep_to_str
from scrounger.utils.general import process
from scrounger.utils.android import devices
from scrounger.utils.config import Log
from scrounger.core.device import AndroidDevice
from time import sleep

# TODO: also look at smali code instead of source

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application implements emulator detector",
        "certainty": 70
    }

    options = [
        {
            "name": "source",
            "description": "local folder containing the application's source",
            "required": True,
            "default": None
        },
        {
            "name": "ignore",
            "description": "paths to ignore, seperated by ;",
            "required": False,
            "default": "/com/google/;/android/support/"
        },
        {
            "name": "apk",
            "description": "local path to the APK file",
            "required": False,
            "default": None
        },
        {
            "name": "identifier",
            "description": "the application's identifier",
            "required": False,
            "default": None
        },
        {
            "name": "avd",
            "description": "the avd name of the emulator to test the module on",
            "required": False,
            "default": None
        }
    ]

    regex = r"generic.*Build\.FINGERPRINT|Build\.FINGERPRINT.*generic|\
sdk.*Build\.PRODUCT|Build\.PRODUCT.*sdk|Secure\.ANDROID_ID|getSensorList"

    def run(self):
        result = {
            "title": "Application Does Not Detect Emulators",
            "details": "",
            "severity": "Medium",
            "report": True
        }

        Log.info("Analysing source for emulator detection mechanisms")
        emulator_detection = pretty_grep(self.regex, self.source)

        if emulator_detection:
            ignore = [filepath.strip() for filepath in self.ignore.split(";")]

            result = {
                "title": "Application Detects Emulators",
                "details": "{}\n\n{}".format(result["details"],
                    pretty_grep_to_str(emulator_detection, self.source,ignore)),
                "severity": "Medium",
                "report": True
            }

        # dynamic testing
        Log.info("Checking requirements for dynamic testing")

        if hasattr(self, "apk") and hasattr(self, "avd") and \
        hasattr(self, "identifier") and self.identifier and \
        self.apk and self.avd:
            # get available devices before starting the emulator
            available_devices = devices()

            # start emulator
            Log.info("Starting the emulator")
            emulator_process = process("emulator -avd {}".format(self.avd))

            # wait for emulator to start
            sleep(60)

            # diff devices -> get emulator
            emulator_id = list(set(devices()) - set(available_devices))

            if len(emulator_id) != 1:
                Log.warn("Could not find the emulator in the device list")
                emulator_process.kill()
                return {
                    "{}_result".format(self.name()): result,
                    "print": "Coud not start emulator or find defined avd"
                }

            device = AndroidDevice(emulator_id)

            Log.info("Installing the apk in the device")
            device.install(self.apk)
            if device.installed(self.identifier):

                while not device.unlocked():
                    Log.info("Please unlock the emulator")
                    sleep(5)

                Log.info("Starting the application")
                device.start(identifier)
                sleep(15)

                if self.identifier not in device.processes():
                    result.update({"report": False})

            emulator_process.kill()

        return {
            "{}_result".format(self.name()): result
        }
