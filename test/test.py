"""
Integration tests for the visualization hub proxies.
"""

import errno
from socket import error as SocketError
import time
import unittest
from selenium.webdriver import Remote
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
try:
    from httplib import BadStatusLine
except ImportError:
    from http.client import BadStatusLine

class IntegrationTest(unittest.TestCase):
    """
    Integration tests that use a remote Selenium driver to connect to the test
    environment of the visualization hub instances.
    """

    MAX_TRIES = 5

    @staticmethod
    def _setup_driver():
        # Connect to the remote executor. Exceptions may be thrown when the
        # Selenium server is not yet set up.
        try:
            return Remote(command_executor='http://127.0.0.1:4444/wd/hub',
                          desired_capabilities=DesiredCapabilities.FIREFOX)
        except BadStatusLine:
            return None
        except SocketError as socket_error:
            if socket_error.errno != errno.ECONNRESET:
                raise

            return None

    def setUp(self):
        self._driver = self._setup_driver()
        tries = 1
        while self._driver is None and tries < self.MAX_TRIES:
            time.sleep(0.5)
            self._driver = self._setup_driver()
            tries += 1

        if self._driver is None:
            self.fail('Could not establish Selenium remote driver')

    def test_reachability(self):
        """
        Test whether the hubs are reachable and serve correct pages.
        """

        driver = self._driver
        driver.get("http://visualization.gros.example")
        self.assertIn("Visualizations from GROS", driver.title)

        driver.get("http://blog.gros.example")
        self.assertIn("GROS project update", driver.title)

        driver.get("http://discussion.gros.example")
        self.assertIn("GROS Discussion", driver.title)

        driver.get("http://prediction.gros.example/api/v1/predict/jira/TEST/sprint/latest")
        self.assertIn("Error 404 Not found", driver.title)

    def tearDown(self):
        self._driver.close()

if __name__ == "__main__":
    unittest.main()
