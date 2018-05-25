from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep, pretty_grep_to_str
from scrounger.utils.android import smali_dirs
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application uses unencrypted \
communications",
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
            "name": "ignore",
            "description": "domains to ignore, seperated by ;",
            "required": False,
            "default": "www.w3;xmlpull.org;www.slf4j"
        }
    ]

    regex = r"http://(-\.)?([^\"^\s/?\.#-]+\.?)+(/[^\s]*)?"

    def run(self):
        result = {
            "title": "Application Communicates Over Unencrypted Channels",
            "details": "",
            "severity": "High",
            "report": False
        }

        # preparing variable to run
        pretty_result = ""
        ignore = [url.strip() for url in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali code")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            urls = pretty_grep(self.regex, smali)
            to_remove = []
            for url in urls:
                for detail in urls[url]:
                    if any(iurl in detail["details"] for iurl in ignore) or \
                    detail["details"] == "http://":
                        urls[url].remove(detail)

                    if not urls[url]:
                        to_remove += [url]

            for filename in to_remove:
                urls.pop(filename)

            pretty_result += pretty_grep_to_str(urls, smali)

        if pretty_result:
            result.update({
                "report": True,
                "details": pretty_result
            })

        return {
            "{}_result".format(self.name()): result
        }
