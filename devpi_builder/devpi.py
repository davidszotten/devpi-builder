# coding=utf-8

"""
Functionality for interacting with a devpi instance.
"""
from __future__ import print_function

import shutil
import subprocess
import tempfile

from wheel.install import WheelFile, BadWheelFile
from wheel.pep425tags import get_supported


class Client(object):
    """
    Wrapper object around the devpi client exposing features required by devpi_builder.
    """
    def __init__(self, index_url, user=None, password=None):
        self._index_url = index_url
        self._user = user
        self._password = password

    def __enter__(self):
        self._client_dir = tempfile.mkdtemp()
        self._execute('use', self._index_url)
        if self._user and self._password is not None:
            self._execute('login', self._user, '--password', self._password)
        return self

    def __exit__(self, *args):
        shutil.rmtree(self._client_dir)

    def _execute(self, *args):
        return subprocess.check_output(
            ['devpi'] + list(args) + ['--clientdir={}'.format(self._client_dir)],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

    def package_version_exists(self, package, version):
        """
        Check whether the given version of the given package is in the index of this client.

        :param package: Python package to check for
        :param version: Version of the package to check for (string)
        :return: True if the exact version of this package is in the index, else False.
        """
        try:
            found = self._execute('list', '{}=={}'.format(package, version)).splitlines()
        except subprocess.CalledProcessError as e:
            if '404' in e.output:
                return False  # package does not exist
            else:
                raise e

        print("looking for {} {}. Found {}. Supported: {}".format(
            package, version, found, get_supported()))
        for item in found:
            try:
                wheel_file = WheelFile(item)
            except BadWheelFile:
                continue

            if wheel_file.compatible:
                return True
        return False

    def upload(self, file):
        """
        Upload the given file to the current index
        """
        self._execute('upload', file)

    def upload_dir(self, dir):
        """
        Upload the given directory to the current index
        """
        self._execute('upload', '--from-dir', dir)

    @property
    def index_url(self):
        return self._index_url
