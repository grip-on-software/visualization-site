"""
Integration tests for the visualization hub proxies.
"""

from contextlib import closing
import errno
from io import BytesIO
import json
from socket import error as SocketError
import time
import unittest
from urllib.request import Request, urlopen
from zipfile import ZipFile
import xmlrunner
from selenium.webdriver import Remote
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
try:
    from httplib import BadStatusLine
except ImportError:
    from http.client import BadStatusLine

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
            return Remote(command_executor=url,
                          desired_capabilities=capabilities)
        except BadStatusLine:
            return None
        except SocketError as socket_error:
            if socket_error.errno != errno.ECONNRESET:
                raise

            return None

    def setUp(self):
        self._driver = self._setup_driver()
        tries = 0
        while self._driver is None and tries < self.DRIVER_POLL_TIMEOUT:
            time.sleep(self.DRIVER_POLL_FREQUENCY)
            self._driver = self._setup_driver()
            tries += self.DRIVER_POLL_FREQUENCY

        if self._driver is None:
            self.fail('Could not establish Selenium remote driver')

        with open('/config.json') as config_file:
            self._config = json.load(config_file)

    def _wait_for(self, condition):
        return WebDriverWait(self._driver, self.WAIT_TIMEOUT,
                             self.WAIT_FREQUENCY).until(condition)

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

    def test_bigboat_status(self):
        """
        Test the BigBoat status visualization.
        """

        driver = self._driver
        driver.get('http://{}/bigboat-status'.format(self._config['visualization_server']))
        self.assertIn("Big Boat status", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'content')))
        self.assertIn("TEST", element.find_element_by_tag_name('h2').text)
        self.assertIn("2017-06-25 17:45:02", element.find_element_by_id('last-checked').text)

    def test_collaboration_graph(self):
        """
        Test the Collaboration graph visualization.
        """

        driver = self._driver
        driver.get('http://{}/collaboration-graph'.format(self._config['visualization_server']))
        self.assertIn("Collaboration Graph", driver.title)

        links = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'svg#graph .links')))
        self.assertEqual(len(links.find_elements_by_tag_name('line')), 3) 
        nodes = driver.find_element_by_css_selector('svg#graph .nodes')
        self.assertEqual(len(nodes.find_elements_by_tag_name('circle')), 5)

    def test_heatmap(self):
        """
        Test the Heatmap visualization.
        """

        driver = self._driver
        driver.get('http://{}/heatmap'.format(self._config['visualization_server']))
        self.assertIn("Calendar/heatmap", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'projectPicker')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 2)

    def test_leaderboard(self):
        """
        Test the Leaderboard visualization.
        """

        driver = self._driver
        driver.get('http://{}/leaderboard'.format(self._config['visualization_server']))
        self.assertIn("Leaderboard", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 1)

    def test_process_flow(self):
        """
        Test the Process flow visualization.
        """

        driver = self._driver
        driver.get('http://{}/process-flow'.format(self._config['visualization_server']))
        self.assertIn("Process flow", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 1)

    def test_timeline(self):
        """
        Test the Timeline visualization.
        """

        driver = self._driver
        driver.get('http://{}/timeline'.format(self._config['visualization_server']))
        self.assertIn("Timeline", driver.title)

        labels = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#chart-holder svg .labels')))
        self.assertEqual(len(labels.find_elements_by_tag_name('text')), 1) 

        weekday = driver.find_element_by_css_selector('[data-weekday-scale]')
        weekday.click()

        self._wait_for(expected_conditions.staleness_of(labels))

        sprint = driver.find_element_by_id('line-drop-0-0')
        hover = ActionChains(driver)
        hover.move_to_element_with_offset(sprint, 1, 1).click().perform()

        tooltip = self._wait_for(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'tooltip')))
        self.assertIn("Start", tooltip.find_element_by_tag_name('h3').text)

        burndown = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#subchart-holder .burndown-chart')))
        self.assertEqual(len(burndown.find_elements_by_tag_name('circle')), 6) 

    def test_navbar(self):
        """
        Test whether the navbar is functional.
        """

        driver = self._driver
        driver.get('http://{}/'.format(self._config['visualization_server']))
        container = driver.find_element_by_id('navbar')
        fullscreen = container.find_element_by_class_name('navbar-fullscreen')
        fullscreen.click()
        self.assertEqual(driver.get_window_position(), {'x': 0, 'y': 0})

    def tearDown(self):
        if self._driver is not None:
            self._driver.save_screenshot('results/{}.png'.format(self.id()))

            for entry in self._driver.get_log('browser'):
                print(entry)

            coverage = self._driver.execute_script("return window.__coverage__")
            if coverage is not None:
                headers = {'Content-Type': 'application/json'}
                request = Request('http://coverage.test:8888/client',
                                  data=json.dumps(coverage).encode('utf-8'),
                                  headers=headers)
                with closing(urlopen(request)) as response:
                    if response.getcode() != 200:
                        self.fail('Could not upload coverage data')

            self._driver.close()

    @classmethod
    def tearDownClass(cls):
        with closing(urlopen('http://coverage.test:8888/download')) as response:
            if response.getcode() != 200:
                print('No coverage data downloaded!')
                for line in response:
                    print(line)
            else:
                with BytesIO(response.read()) as zip_data:
                    with ZipFile(zip_data, 'r') as zip_file:
                        zip_file.extractall('coverage/')


def main():
    """
    Main entry point.
    """

    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='junit'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False)

if __name__ == "__main__":
    main()
