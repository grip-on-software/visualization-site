"""
Base classes for the integration test suite for the visualizations.
"""

from contextlib import closing
import errno
import html
import json
import os.path
import re
import linecache
from socket import error as SocketError
import time
import unittest
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from selenium.webdriver import Remote
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from axe_selenium_python import Axe
from .reporter import Reporter

try:
    from httplib import BadStatusLine
except ImportError:
    from http.client import BadStatusLine

def skip_unless_visualization(name):
    """
    Skip a test unless a visualization with the given `name` is under test,
    i.e., it is part of the produced output.
    """

    visualization_names = linecache.getline('/visualization_names.txt', 1)
    if name in visualization_names.rstrip().split(' '):
        return lambda func: func

    return unittest.skip("Visualization {} is not under test".format(name))

class IntegrationTest(unittest.TestCase):
    """
    Integration tests that use a remote Selenium driver to connect to the test
    environment of the visualization hub instances.
    """

    DRIVER_POLL_TIMEOUT = 2.5
    DRIVER_POLL_FREQUENCY = 0.5

    WAIT_TIMEOUT = 5
    WAIT_FREQUENCY = 0.5

    @staticmethod
    def _setup_driver():
        # Connect to the remote executor. Exceptions may be thrown when the
        # Selenium server is not yet set up.
        try:
            url = 'http://selenium.test:4444/wd/hub'
            capabilities = DesiredCapabilities.CHROME
            capabilities['loggingPrefs'] = {'browser': 'ALL'}
            options = Options()
            options.add_experimental_option("prefs", {
                "download.default_directory": "/work/downloads",
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            return Remote(command_executor=url,
                          desired_capabilities=capabilities,
                          options=options)
        except BadStatusLine:
            return None
        except SocketError as socket_error:
            if socket_error.errno != errno.ECONNRESET:
                raise

            return None

    def _get_url(self, key):
        org = os.getenv('VISUALIZATION_ORGANIZATION')
        combined = os.getenv('VISUALIZATION_COMBINED')
        base = 'http://{}'.format(self._config['{}_server'.format(key)])

        if combined == "true":
            url = self._config['{}_url'.format(key)].replace('/$organization',
                                                             '/combined')
        else:
            url = re.sub(r'(/)?\$organization',
                         r'\1{}'.format(org) if org is not None else '',
                         self._config['{}_url'.format(key)])

        return urljoin(base, url)

    def setUp(self):
        self._driver = self._setup_driver()
        tries = 0
        while self._driver is None and tries < self.DRIVER_POLL_TIMEOUT:
            time.sleep(self.DRIVER_POLL_FREQUENCY)
            self._driver = self._setup_driver()
            tries += self.DRIVER_POLL_FREQUENCY

        if self._driver is None:
            self.fail('Could not establish Selenium remote driver')

        self._driver.set_window_size(1366, 768)

        with open('/config.json') as config_file:
            self._config = json.load(config_file)

        self._visualization_url = self._get_url('visualization')
        self._prediction_url = self._get_url('prediction')

    def _wait_for(self, condition, message=''):
        return WebDriverWait(self._driver, self.WAIT_TIMEOUT,
                             self.WAIT_FREQUENCY).until(condition, message)

    def tearDown(self):
        if self._driver is not None:
            self._driver.save_screenshot('results/{}.png'.format(self.id()))
            Reporter.write_result(self.id())

            Reporter.write_log(self.id(), self._driver.get_log('browser'))

            coverage = self._driver.execute_script("return window.__coverage__")
            if coverage is not None:
                headers = {'Content-Type': 'application/json'}
                request = Request('http://coverage.test:8888/client',
                                  data=json.dumps(coverage).encode('utf-8'),
                                  headers=headers)
                response = urlopen(request)
                with closing(response):
                    if response.getcode() != 200:
                        self.fail('Could not upload coverage data')

            axe = Axe(self._driver, script_url='/axe-core/axe.min.js')
            axe.inject()
            accessibility = axe.run(options=json.dumps({
                'rules': {
                    # Axe considers all anchor links to be skip links
                    'skip-link': {'enabled': False}
                }
            }))
            axe.write_results(accessibility,
                              'accessibility/{}.json'.format(self.id()))

            report = html.escape(axe.report(accessibility["violations"]))
            Reporter.write_accessibility(self.id(), report)

            self._driver.close()
