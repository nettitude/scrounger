from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep
from scrounger.utils.android import smali_dirs
from scrounger.utils.android import extract_smali_method
from scrounger.utils.config import Log, _CERT_PATH
from scrounger.lib.proxy2 import create_server

import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application implements ssl pinning",
        "certainty": 50
    }

    options = [
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
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
            "name": "identifier",
            "description": "the application's identifier",
            "required": False,
            "default": None
        },
        {
            "name": "device",
            "description": "the remote device",
            "required": False,
            "default": None
        },
        {
            "name": "proxy_host",
            "description": "the hostname to have a proxy listening on",
            "required": False,
            "default": ""
        },
        {
            "name": "proxy_port",
            "description": "the port to have a proxy listening on",
            "required": False,
            "default": 9090
        },
        {
            "name": "wait_time",
            "description": "set how long (seconds) to wait before starting the \
proxy - this time is used to allow setup of proxy on the remote device.",
            "required": False,
            "default": 20
        },
        {
            "name": "ignore_url",
            "description": "domains to be ignored",
            "required": False,
            "default": ".icloud.com;.apple.com;.googleapis.com;\
graph.facebook.com;.crashlytics.com;api.branch.io;t.appsflyer.com;\
gate.hockeyapp.net;www.paypalobjects.com;www.gstatic.com;app.adjust.com;\
data.flurry.com;.doubleclick.net;.google-analytics.com;.adobedtm.com;\
googletagmanager.com"
        },
    ]

    regex = r"X509TrustManager|getAcceptedIssuers|checkClientTrusted|\
checkServerTrusted"
    mock_check_server = r".method.*checkServerTrusted(.*\n)*?[ \t]*\.\
prologue\n(([\t ]*(\.line.*)?)\n)*[ \t]*return-void"
    mock_accepted_issuers = r".method.*getAcceptedIssuers(.*\n)*?[ \t]*\.\
prologue\n(([\t ]*(\.line.*)?)\n)*[ \t]*const\/4 v0, 0x0\n[ \n\t]*\
return-object v0"

    def run(self):
        from time import sleep
        result = {
            "title": "Application Does Not Implement SSL Pinning",
            "details": "",
            "severity": "High",
            "report": False
        }

        # preparing variable to run
        ssl_keywords = {}
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]
        ignored_urls = [url.strip() for url in self.ignore_url.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali for SSL evidences")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            ssl_keywords.update(pretty_grep(self.regex, smali))

        if not ssl_keywords:
            result.update({
                "report": True,
                "details": "Found no evidences of a `TrustManager`."
            })

        Log.info("Analysing SSL evidences")

        for filename in ssl_keywords:
            if any(filepath in filename for filepath in ignore):
                continue

            with open(filename, "r") as fp:
                smali = fp.read()

            if re.search(self.mock_check_server, smali):
                result.update({
                    "report": True,
                    "details": "{}\n* {}:{}\n".format(
                        result["details"],
                        filename.replace(self.decompiled_apk, ""),
                        extract_smali_method("checkServerTrusted", filename)
                    )
                })

            if re.search(self.mock_accepted_issuers, smali):
                result.update({
                    "report": True,
                    "details": "{}\n* {}:{}\n".format(
                        result["details"],
                        filename.replace(self.decompiled_apk, ""),
                        extract_smali_method("getAcceptedIssuers", filename)
                    )
                })

        if self.device and self.identifier and \
        self.proxy_host != None and self.proxy_port != None:
            Log.info("Testing SSL Pinning using a proxy")
            Log.info("Make sure your device trusts the CA in: {}/ca.crt".format(
                _CERT_PATH))
            Log.info("Waiting for {} seconds to allow time to setup the \
proxy on the remote device".format(self.wait_time))
            sleep(int(self.wait_time))

            Log.info("Killing the application")
            self.device.stop(self.identifier)

            Log.info("Starting the SSL proxy")
            try:
                proxy_server = create_server(self.proxy_host, self.proxy_port,
                    _CERT_PATH)
            except Exception:
                import traceback
                Log.debug(traceback.format_exc())

            Log.info("Starting the Application")
            self.device.start(self.identifier)

            Log.info("Waiting for the Application to start and make requests")
            sleep(10)

            unfiltered_pinned = list(set(proxy_server.server.connected) -
                set(proxy_server.server.requested))
            pinned = []
            for url in unfiltered_pinned:
                if not any([u in url for u in ignored_urls]):
                    pinned += [url]

            if not proxy_server.server.connected:
                Log.error("No connections made by the application")

            if pinned:
                result.update({
                    "title": "Application Implements SSL Pinning",
                    "report": True,
                    "details": "{}\n\nThe application started a connection but \
made no requests to the following domains:\n* {}".format(result["details"],
                        "\n* ".join(pinned))
                    })

            if proxy_server.server.requested:
                result.update({
                    "report": True,
                    "details": "{}\n\nThe application started a connection and \
made requests to the following domains:\n* {}".format(result["details"],
                        "\n* ".join(proxy_server.server.requested))
                    })

            proxy_server.stop()

        return {
            "{}_result".format(self.name()): result
        }
