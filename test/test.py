"""
Integration tests for the visualization hub proxies.
"""

import errno
import json
from socket import error as SocketError
import time
import unittest
import xmlrunner
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
            url = 'http://selenium.test:4444/wd/hub'
            return Remote(command_executor=url,
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

        with open('config.json') as config_file:
            self._config = json.load(config_file)

    def test_reachability(self):
        """
        Test whether the hubs are reachable and serve correct pages.
        """

        driver = self._driver
        driver.get('http://{}/'.format(self._config['visualization_server']))
        self.assertIn("Visualizations from GROS", driver.title)

        if 'blog_url' in self._config and self._config['blog_url']:
            driver.get(self._config['blog_url'])
            self.assertIn("GROS project update", driver.title)

        if 'discussion_url' in self._config and self._config['discussion_url']:
            driver.get(self._config['discussion_url'])
            self.assertIn("GROS Discussion", driver.title)

        driver.get("http://{}/api/v1/predict/jira/TEST/sprint/latest".format(self._config['prediction_server']))
        self.assertIn("Not found", driver.title)

    def tearDown(self):
        if self._driver is not None:
            self._driver.save_screenshot('results/{}.png'.format(self.id()))
            self._driver.close()

if __name__ == "__main__":
    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='junit'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False)
