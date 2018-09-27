#! /usr/bin/env python

from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools import setup, find_packages
from scrounger.utils.config import _VERSION, _SCROUNGER_HOME

def _create_custom_modules_paths():
    from scrounger.utils.general import execute
    from os import path

    current_path = path.realpath(__file__).rsplit('/', 1)[0]
    modules_path = "{}/scrounger/modules/".format(current_path)

    # create custom module paths
    module_types = execute("find {} -type d".format(modules_path))
    for module_type in module_types.split("\n"):
        custom_path = "{}/modules/custom/{}".format(_SCROUNGER_HOME,
            module_type.replace(modules_path, ""))
        execute("mkdir -p {}".format(custom_path))

        # add __init__.py to be able to import modules
        execute("touch {}/__init__.py".format(custom_path))

    # copy ios binaries
    ios_binaries_path = "{}/bin/ios/".format(current_path)
    installed_path = "{}/bin/ios".format(_SCROUNGER_HOME)
    execute("mkdir -p {}".format(installed_path))

    binaries = execute("find {} -type f".format(ios_binaries_path))
    for binary in binaries.split("\n"):
        execute("cp {} {}".format(binary, installed_path))

    # copy android binaries
    android_binaries_path = "{}/bin/android/".format(current_path)
    installed_path = "{}/bin/android".format(_SCROUNGER_HOME)
    execute("mkdir -p {}".format(installed_path))

    binaries = execute("find {} -type f".format(android_binaries_path))
    for binary in binaries.split("\n"):
        execute("cp {} {}".format(binary, installed_path))

class _pre_install(install):
    def run(self):
        _create_custom_modules_paths()
        install.run(self)

class _pre_develop(develop):
    def run(self):
        _create_custom_modules_paths()
        develop.run(self)

setup(
    name="scrounger",
    version=_VERSION,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "scrounger = scrounger.console.cli:_main",
            "scrounger-console = scrounger.console.interactive:_main"
        ]
    },
    cmdclass={
        'install': _pre_install,
        'develop': _pre_develop,
    },
    author="Ruben de Campos",
    author_email="rdecampos@nettitude.com",
    description="Scrounger - a person who borrows from or lives off others.",
    keywords=["android", "ios", "mobile applications", "mobile assessments",
        "apk", "ipa", "security"],
    long_description="""
Scrounger - a person who borrows from or lives off others.
Scrounger will leech all security issues from Android and iOS applications.
    """,
    install_requires=["paramiko", "biplist", "langdetect"]
)

