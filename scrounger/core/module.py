"""
This module contains the base calsses to be extended when developing checks for
scrougner to run on mobile applications.

They must contain a `meta` and `options` variables and a `run` method

The `meta` variable must be of format:
{
    "author": str,
    "decription": str,
    "certainty": int, # > 0 and <= 100
}

The `options` variable must be in the format:
{
    "name": "variable_name",
    "description": "what it is",
    "required": True|False,
    "default": "default"|None,
}

If the module requires a device to be connected you can include a `device`
option, e.g.:
{
    "name": "device",
    "description": "the remote device",
    "required": True,
    "default": None
}

This option will be checked against scrounger's device module vefore running the
module.

The `result` returned by `run` for an analysis module must be of format:
{
    "title": "Title of the issue",
    "details": "Details of the issue",
    "severity": "Severity of the issue",
    "report": True|False
}

"""

def validate_analysis_result(result):
    """
    Checks if a given result is a valid result by checking if all required
    fields are in the result dict

    :param dict result: the dict result to be checked
    :return: True if all fields are in the result or False if not
    """
    REQUIRED_FIELDS = ["title", "details", "severity", "report"]

    return isinstance(result, dict) and all(
        field in REQUIRED_FIELDS for field in result)

class MissingFieldException(Exception):
    """
    Exception used when a variable or method is missing from the Module
    definition
    """
    pass

class MisconfiguredVariable(Exception):
    """
    Exception raised when the meta or options variable has been misconfigured
    """
    pass

class MissingRequiredOptionsException(Exception):
    """
    Exception used when trying to run a module without the requires options
    defined
    """

    missing_options = None
    """ Variable Used to save the missing options """

    def __init__(self, message, missing_options):
        """
        Creates an exception and saves the missing options into a variable
        """
        super(MissingRequiredOptionsException, self).__init__(message)
        self.missing_options = missing_options


class BaseModule(object):
    _init_called = False

    def __init__(self):
        """
        Creates a module object and checks if the required variables and methods
        are defined
        """

        # check for meta and options variables first
        REQUIRED_VARIABLES = ["meta", "options"]
        for variable in REQUIRED_VARIABLES:
            if not hasattr(self, variable):
                raise MissingFieldException(
                    "Missing the `{}` variable when defining a module".format(
                        variable))

        # check for requires methods
        REQUIRED_METHODS = ["run", "validate_options"]
        for method in REQUIRED_METHODS:
            if not hasattr(self, method):
                raise MissingFieldException(
                    "Missing the `{}` method when defining a module".format(
                        method))

        # check if meta variable has all the necessary values and are valid
        REQUIRED_META_FIELDS = {
            "author": str, "description": str, "certainty": int
        }

        for field in REQUIRED_META_FIELDS:
            # check if any missing fields

            if field not in self.meta:
                raise MisconfiguredVariable(
                    "Field `{}` is missing from the `meta` variable".format(
                        field))

            # check if values are valid
            if not isinstance(self.meta[field], REQUIRED_META_FIELDS[field]):
                from scrounger.utils.general import execute
                execute("echo Meta: {} >> /tmp/debug.log".format(self.meta))
                raise MisconfiguredVariable(
                    "Metafield `{}` is not of type `{}`".format(
                        field, REQUIRED_META_FIELDS[field]))

        # check if certainty is > 0 and <= 100
        if self.meta["certainty"] < 0 or self.meta["certainty"] > 100:
            raise MisconfiguredVariable(
                "Certainty must be a value between 0 and 100")

        # check if additional options are valid
        required_fields = ["name", "description", "required", "default"]
        for option in self.options:
            for field in required_fields:
                if field not in option:
                    raise MisconfiguredVariable(
                        "Field `{}` not found in option `{}`".format(
                            field, option))

            # check if var name has spaces
            if " " in option["name"]:
                raise MisconfiguredVariable(
                    "Option `{}` contains spaces".format(option["name"]))

        self._init_called = True

    def validate_options(self):
        """
        Checks if the required options are set up before running the module and
        raises exceptions if anything has been misconfigured

        :return: nothing
        """
        from scrounger.core.device import BaseDevice

        if not self._init_called:
            raise Exception("Super class `__init__` method not called")

        # check if required options are set
        for option in self.options:
            if option["required"] and (not hasattr(self, option["name"]) or \
                getattr(self, option["name"]) == None):
                raise MissingRequiredOptionsException(
                    "Option `{}` not set".format(option["name"]), option)

        # check if device is of type device
        if hasattr(self, "device") and not isinstance(self.device, BaseDevice):
            raise Exception(
                "Option `device` is not of type `scrounger.core.device`")

    def name(self):
        return self.__module__.replace("scrounger.modules.", "")

