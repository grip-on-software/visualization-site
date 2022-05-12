"""
Integration tests for the visualization hub proxies.

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

import sys
import unittest
import xmlrunner
import suite
from suite.reporter import Reporter

def load_tests(loader, tests, pattern):
    """
    Load tests from the test suite.
    """

    tests.addTests(loader.loadTestsFromModule(suite, pattern))
    return tests

def main():
    """
    Main entry point.
    """

    Reporter.setup()
    program = unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='junit'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False, exit=False)
    Reporter.close()
    return 0 if program.result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())
