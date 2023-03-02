"""
Base classes for the integration test suite for the visualizations.

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

from contextlib import closing
import errno
import html
from http.client import BadStatusLine
import json
import os
import re
import linecache
from socket import error as SocketError
import time
import unittest
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from selenium.webdriver import Remote
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.support.wait import WebDriverWait
from axe_selenium_python import Axe

def skip_unless_visualization(name):
    """
    Skip a test unless a visualization with the given `name` is under test,
    i.e., it is part of the produced output.
    """

    visualization_names = linecache.getline('/visualization_names.txt', 1)
    if name in visualization_names.rstrip().split(' '):
        return lambda func: func

    return unittest.skip(f"Visualization {name} is not under test")

class IntegrationTest(unittest.TestCase):
    """
    Integration tests that use a remote Selenium driver to connect to the test
    environment of the visualization hub instances.
    """

    # Timeout and poll frequency for setting up the remote driver.
    DRIVER_POLL_TIMEOUT = 2.5
    DRIVER_POLL_FREQUENCY = 0.5

    # Global connection timeout for the remote driver.
    CONNECTION_TIMEOUT = 10

    # Timeout and poll frequency for waiting for element changes.
    WAIT_TIMEOUT = 5
    WAIT_FREQUENCY = 0.5

    @staticmethod
    def _setup_driver():
        # Connect to the remote executor. Exceptions may be thrown when the
        # Selenium server is not yet set up.
        try:
            url = 'http://selenium.test:4444'
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
        base = f"http://{self._config[f'{key}_server']}"

        if combined == "true":
            url = self._config[f'{key}_url'].replace('/$organization',
                                                     '/combined')
        else:
            url = re.sub(r'(/)?\$organization',
                         rf'\1{org}' if org is not None else '',
                         self._config[f'{key}_url'])

        return urljoin(base, url)

    def setUp(self):
        RemoteConnection.set_timeout(self.CONNECTION_TIMEOUT)
        self._driver = self._setup_driver()
        tries = 0
        while self._driver is None and tries < self.DRIVER_POLL_TIMEOUT:
            time.sleep(self.DRIVER_POLL_FREQUENCY)
            self._driver = self._setup_driver()
            tries += self.DRIVER_POLL_FREQUENCY

        if self._driver is None:
            self.fail('Could not establish Selenium remote driver')

        self._driver.set_window_size(1366, 768)

        with open('/config.json', encoding='utf-8') as config_file:
            self._config = json.load(config_file)

        self._visualization_url = self._get_url('visualization')
        self._prediction_url = self._get_url('prediction')

    def _wait_for(self, condition, message=''):
        return WebDriverWait(self._driver, self.WAIT_TIMEOUT,
                             self.WAIT_FREQUENCY).until(condition, message)

    def tearDown(self):
        if self._driver is None or self._outcome is None or \
            self._outcome.result is None or \
            getattr(self._outcome.result, 'reporter', None) is None:
            if self._driver is not None:
                self._driver.quit()
                self._driver = None
            return

        reporter = self._outcome.result.reporter
        self._driver.save_screenshot(f'results/{self.id()}.png')
        reporter.write_result(self.id())

        reporter.write_log(self.id(), self._driver.get_log('browser'))

        coverage = self._driver.execute_script("return window.__coverage__")
        if coverage is not None:
            headers = {'Content-Type': 'application/json'}
            request = Request('http://coverage.test:8888/client',
                              data=json.dumps(coverage).encode('utf-8'),
                              headers=headers)
            try:
                with closing(urlopen(request)) as response:
                    status_code = response.getcode()
                    if status_code != 200:
                        self.fail('Could not upload coverage data: server '
                                  f'responsed with status code {status_code}')
            except URLError as error:
                self.fail(f'Could not upload coverage data: {error}')

        axe = Axe(self._driver, script_url='/axe-core/axe.min.js')
        axe.inject()
        accessibility = axe.run(options=json.dumps({
            'rules': {
                # Axe considers all anchor links to be skip links
                'skip-link': {'enabled': False}
            }
        }))
        axe.write_results(accessibility,
                          f'accessibility/{self.id()}.json')

        report = html.escape(axe.report(accessibility["violations"]))
        reporter.write_accessibility(self.id(), report)

        self._driver.quit()
        self._driver = None
