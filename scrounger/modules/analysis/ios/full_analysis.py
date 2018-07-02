from scrounger.core.module import BaseModule, validate_analysis_result

# helper functions / modules
from scrounger.utils.general import execute
from scrounger.utils.config import Log
from json import dumps
from os import listdir

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Runs all modules in analysis and writes a report into \
the output directory",
        "certainty": 100
    }

    options = [
        {
            "name": "output",
            "description": "local output directory",
            "required": True,
            "default": "/tmp"
        },
    ]

    _analysis_modules = []
    _output_directory = "/ios.analysis"

    def __init__(self):
        import scrounger.modules.analysis.ios as ios_analysis
        all_modules = ios_analysis.__all__

        for module in all_modules:
            module_class = __import__(
                "scrounger.modules.analysis.ios.{}".format(module),
                fromlist=["Module"])

            # avoid running full_analysis again
            if self.__module__ == module_class.__name__:
                continue

            self._analysis_modules += [module_class]

            self.options += module_class.Module.options
            sanitized_options = {}
            for option in self.options:
                if option["name"] not in sanitized_options:
                    sanitized_options[option["name"]] = option
                elif option["name"] in sanitized_options and \
                not sanitized_options[option["name"]]["required"] and \
                option["required"]:
                    sanitized_options[option["name"]]["required"] = True

            self.options = sanitized_options.values()

        super(Module, self).__init__()

    def validate_options(self):
        """
            This module should try to run even if the required variables are
            not set
        """
        return True

    def run(self):
        results = []
        exceptions = []

        # run all modules
        Log.info("Running all iOS analysis modules")
        for module in self._analysis_modules:

            instance = module.Module()
            for option in self.options:
                if hasattr(self, option["name"]):
                    setattr(instance, option["name"],
                        getattr(self, option["name"]))

            try:
                instance.validate_options()
                run_result = instance.run()

                for key in run_result:
                    if key.endswith("_result") and validate_analysis_result(
                        run_result[key]) and run_result[key]["report"]:
                        results += [run_result[key]]
            except Exception as e:
                exceptions += [{"module": instance.name(), "exception": e}]

        # setup output folders
        Log.info("Creating output folders")
        output_directory = "{}{}".format(self.output, self._output_directory)
        execute("mkdir -p {}".format(output_directory))
        output_file = "{}/results.json".format(output_directory)

        # write results to json file
        Log.info("Writing results to file")
        with open(output_file, "w") as fp:
            fp.write(dumps(results))

        return {
            "ios_analysis": results,
            "exceptions": exceptions,
            "print": "The following issues were found:\n* {}".format(
                "\n* ".join([result["title"] for result in results])
            )
        }

"""
set global apk a.apk
set global decompiled_apk output/a.decompiled
set global source output/a.source
set global identifier com.pcsl.mybanking
set global output ./other-output
set global smali output/a.decompiled/smali
add_device ios 00cd7e67ec57c127
set global device 1
use analysis/ios/full_analysis
run

"""
