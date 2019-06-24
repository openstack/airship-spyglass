# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

LOG = logging.getLogger(__name__)


class SpyglassBaseException(Exception):
    """Base Spyglass exception"""

    message = 'Base Spyglass exception.'

    def __init__(self, message=None, **kwargs):
        self.message = message or self.message
        try:
            self.message = self.message.format(**kwargs)
        except KeyError:
            LOG.warning('Missing kwargs')
        super().__init__(self.message)


class UnsupportedPlugin(SpyglassBaseException):
    """Exception that occurs when a plugin is called that does not exist

    :param plugin_name: name of the specified plugin
    :param entry_point: the package used to access plugin_name
    """
    message = (
        '%(plugin_name) was not found in the package %(entry_point) '
        'entry points.')


# Data Extractor exceptions


class InvalidIntermediary(SpyglassBaseException):
    """Exception that occurs when data is missing from the intermediary file

    :param key: dictionary key that Spyglass attempted to access
    """
    message = '%(key) is not defined in the given intermediary file.'


# Validator exceptions


class PathDoesNotExistError(SpyglassBaseException):
    """Exception that occurs when the document or schema path does not exist

    :param file_type: type of the files being accessed, documents or schemas
    :param path: nonexistent path attempted to access
    """
    message = '%(file_type) path: %(path) does not exist.'


class UnexpectedFileType(SpyglassBaseException):
    """Exception that occurs when an unexpected file type is given

    :param found_ext: the extension of the file given
    :param expected_ext: the extension that was expected for the file
    """
    message = (
        'Unexpected file type %(found_ext), '
        'expected type %(expected_ext)')


class DirectoryEmptyError(SpyglassBaseException):
    """Exception for when a directory is empty

    This exception can occur when either a directory is empty or if a directory
    does not have any files with the correct file extension.

    :param ext: file extension being searched for
    :param path: path being searched for files of the specified extension
    """
    message = 'No files with %(ext) extension found in document path %(path)'
