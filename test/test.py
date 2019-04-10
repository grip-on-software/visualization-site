"""
Integration tests for the visualization hub proxies.
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
