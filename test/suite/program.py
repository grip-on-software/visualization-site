"""
Test program.

Copyright 2017-2020 ICTU
Copyright 2017-2022 Leiden University

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from xmlrunner.runner import XMLTestProgram
from .runner import Runner

class Program(XMLTestProgram):
    """
    Test program.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('testRunner', Runner)
        self._main_parser = None
        self._discovery_parser = None
        self.output = 'junit'
        self.output_file = None
        self.outsuffix = None
        super().__init__(*args, **kwargs)

    def _parseKnownArgs(self, kwargs):
        pass

    def _initArgParsers(self):
        # Restore unittest.TestRunner behavior (no extra arguments)
        parent_parser = self._getParentArgParser()
        self._main_parser = self._getMainArgParser(parent_parser)
        self._discovery_parser = self._getDiscoveryArgParser(parent_parser)

    def runTests(self):
        try:
            super().runTests()
        finally:
            if isinstance(self.testRunner, Runner):
                self.testRunner.cleanup()
