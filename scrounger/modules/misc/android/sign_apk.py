from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.android import sign
from scrounger.utils.config import Log, _SCROUNGER_HOME

from scrounger.modules.misc.android.app.manifest import Module as ManifestModule

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Recompiles a decompiled application",
        "certainty": 100
    }

    options = [
        {
            "name": "recompiled_apk",
            "description": "local path to the apk to recompile",
            "required": True,
            "default": None
        },
        {
            "name": "output",
            "description": "local output directory",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        Log.info("Preparing to sign the application")

        binaries_local_path = "{}/bin/android".format(_SCROUNGER_HOME)
        signjar = "{}/signapk.jar".format(binaries_local_path)
        key = "{}/key.pk8".format(binaries_local_path)
        cert = "{}/cert.x509.pem".format(binaries_local_path)

        # get identifier
        identifier = self.recompiled_apk.rsplit("/",1)[-1].rsplit(".", 1)[0]
        signed_apk = "{}/{}-signed.apk".format(self.output, identifier)

        # sign
        Log.info("Signinging application")
        output = sign(self.recompiled_apk, signed_apk, signjar, cert, key)

        if output and "Exception" in output:
            return {
                "print": "Failed to sign the application:\n{}".format(output)
            }

        return {
            "{}_signed".format(identifier): signed_apk,
            "print": "Application signed to {}".format(signed_apk)
        }

