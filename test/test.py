"""
Integration tests for the visualization hub proxies.
"""

from contextlib import closing
import errno
from io import BytesIO
import json
import os.path
from socket import error as SocketError
import time
import unittest
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zipfile import ZipFile
import xmlrunner
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Remote
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
try:
    from httplib import BadStatusLine
except ImportError:
    from http.client import BadStatusLine

class SprintReportExportTest:
    """
    Test case for a sprint report export mechanism.
    """

    def __init__(self, driver):
        self._driver = driver

    def test(self, button):
        """
        Test an export after clicking its associated button.
        """

        raise NotImplementedError('Must be implemented by subclass')

    def get_message(self, exporter):
        """
        Provide a message for unittest assertions.
        """

        raise NotImplementedError('Must be implemented by subclass')

class SprintReportExportFilename(SprintReportExportTest):
    """
    Test case for a sprint report export file download.
    """

    def __init__(self, driver, options):
        super(SprintReportExportFilename, self).__init__(driver)
        self.options = {
            'filename': 'sprint-report',
            'path': '/work/downloads',
            'timeout': 5,
            'poll_frequency': 0.5
        }
        self.options.update(options)

    def test(self, button):
        path = os.path.join(self.options['path'], self.options['filename'])
        wait = WebDriverWait(self._driver, self.options['timeout'],
                             self.options['poll_frequency'])
        try:
            wait.until(lambda driver: os.path.exists(path))
        except TimeoutException:
            return False

        return True

    def get_message(self, exporter):
        return '{path}/{filename} exists within {timeout} seconds after clicking {export} export'.format(export=exporter, **self.options)

class SprintReportExportAttribute(SprintReportExportTest):
    """
    Test case for a sprint report export attribute change.
    """

    def __init__(self, driver, attribute, value):
        super(SprintReportExportAttribute, self).__init__(driver)
        self.attribute = attribute
        self.value = value

    def test(self, button):
        return button.get_attribute(self.attribute) == self.value

    def get_message(self, exporter):
        return '{} export has attribute {}={}'.format(exporter, self.attribute, self.value)

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

    @classmethod
    def setUpClass(cls):
        cls._results_index = open('results/index.html', 'w')
        cls._results_index.write('<!doctype html><html><head>')
        cls._results_index.write('<meta charset="utf-8">')
        cls._results_index.write('<title>Visualization test results</title>')
        cls._results_index.write('</head><body><h1>Test results</h1><ul>')

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

        visualization = 'http://{}'.format(self._config['visualization_server'])
        self._visualization_url = urljoin(visualization,
                                          self._config['visualization_url'])

        prediction = 'http://{}'.format(self._config['prediction_server'])
        self._prediction_url = urljoin(prediction,
                                       self._config['prediction_url'])

    def _wait_for(self, condition, message=''):
        return WebDriverWait(self._driver, self.WAIT_TIMEOUT,
                             self.WAIT_FREQUENCY).until(condition, message)

    def test_reachability(self):
        """
        Test whether the hubs are reachable and serve correct pages.
        """

        driver = self._driver
        driver.get(self._visualization_url)
        self.assertIn("Visualizations from GROS", driver.title)

        if 'blog_url' in self._config and self._config['blog_url']:
            driver.get(self._config['blog_url'])
            self.assertIn("GROS project update", driver.title)

        if 'discussion_url' in self._config and self._config['discussion_url']:
            driver.get(self._config['discussion_url'])
            self.assertIn("GROS Discussion", driver.title)

        driver.get("{}/api/v1/predict/jira/TEST/sprint/latest".format(self._prediction_url))
        self.assertIn("Not found", driver.title)

    def test_bigboat_status(self):
        """
        Test the BigBoat status visualization.
        """

        driver = self._driver
        driver.get('{}/bigboat-status'.format(self._visualization_url))
        self.assertIn("Big Boat status", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'content')))
        self.assertIn("TEST", element.find_element_by_tag_name('h2').text)
        self.assertEqual("http://www.dashboard.test/", element.find_element_by_id('source-url').get_attribute('href'))
        self.assertIn("2017-06-27 09:00:39", element.find_element_by_id('last-checked').text)

        graph = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'average-reliability')))
        ActionChains(driver).move_to_element_with_offset(graph, 480, 10).perform()

        focus = self._wait_for(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'focus')))
        self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '.focus tspan')))
        self.assertEqual(focus.find_element_by_css_selector('tspan:first-child').text, '26 Jun 18:31')
        self.assertEqual(focus.find_element_by_css_selector('tspan:last-child').text, 'Available IPs')
        self.assertEqual(focus.get_attribute('transform'), 'translate(568,450)')

    def test_collaboration_graph(self):
        """
        Test the Collaboration graph visualization.
        """

        driver = self._driver
        driver.get('{}/collaboration-graph'.format(self._visualization_url))
        self.assertIn("Collaboration Graph", driver.title)

        links = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'svg#graph .links')))
        self.assertEqual(len(links.find_elements_by_tag_name('line')), 3)
        nodes = driver.find_element_by_css_selector('svg#graph .nodes')
        self.assertEqual(len(nodes.find_elements_by_tag_name('circle')), 5)

    def test_collaboration_graph_extern(self):
        """
        Test the external filter mechanism of the Collaboration graph.
        """

        driver = self._driver
        driver.get('{}/collaboration-graph'.format(self._visualization_url))

        nodes = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'svg#graph .nodes')))
        circle = nodes.find_elements_by_tag_name('circle')[2]

        button = driver.find_element_by_css_selector('.regular-option')
        button.click()
        self._wait_for(expected_conditions.invisibility_of_element_located(circle))

        self.assertEqual(circle.get_attribute('visibility'), 'collapse')

    def test_collaboration_graph_find(self):
        """
        Test the search mechanism of the Collaboration graph.
        """

        driver = self._driver
        driver.get('{}/collaboration-graph'.format(self._visualization_url))

        nodes = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'svg#graph .nodes')))
        circles = nodes.find_elements_by_tag_name('circle')

        search = driver.find_element_by_css_selector('input.regular-option')
        search.send_keys('A')

        time.sleep(3)
        self.assertEqual(circles[2].get_attribute('fill'), 'red')

    def test_collaboration_timelapse(self):
        """
        Test the timelapse mechanism of the Collaboration graph.
        """

        driver = self._driver
        driver.get('{}/collaboration-graph'.format(self._visualization_url))

        button = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#options .button')))
        button.click()

        self.assertEqual(len(driver.find_elements_by_css_selector('.regular-option[disabled]')), 2)

        buttons = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#options .buttons')))
        pause = buttons.find_element_by_id('pauseButton')
        slower = buttons.find_element_by_css_selector('.slower')
        faster = buttons.find_element_by_css_selector('.faster')

        self.assertEqual(pause.get_attribute("data-tooltip"), "Pause")
        self.assertIsNone(slower.get_attribute("disabled"))
        self.assertIsNone(faster.get_attribute("disabled"))

        faster.click()
        faster.send_keys("+")
        faster.click()

        self.assertTrue(faster.get_attribute("disabled"))

        slower.click()
        self.assertFalse(faster.get_attribute("disabled"))

        title = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#options h3')))
        self.assertEqual(title.text, "August 2017")

        links = driver.find_element_by_css_selector('svg#graph .links')
        self.assertEqual(len(links.find_elements_by_tag_name('line')), 2)
        nodes = driver.find_element_by_css_selector('svg#graph .nodes')
        self.assertEqual(len(nodes.find_elements_by_tag_name('circle')), 3)

        self._wait_for(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '.fa-stop')))
        self.assertEqual(pause.get_attribute("data-tooltip"), "Stopped")

        button.click()
        self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'svg#graph .nodes .node:nth-child(5)')))

        links = driver.find_element_by_css_selector('svg#graph .links')
        self.assertEqual(len(links.find_elements_by_tag_name('line')), 3)
        nodes = driver.find_element_by_css_selector('svg#graph .nodes')
        self.assertEqual(len(nodes.find_elements_by_tag_name('circle')), 5)

    def test_heatmap(self):
        """
        Test the Heatmap visualization.
        """

        driver = self._driver
        driver.get('{}/heatmap'.format(self._visualization_url))
        self.assertIn("Calendar/heatmap", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'projectPicker')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 2)


    def test_heatmap_tooltip(self):
        """
        Test the tooltips of individual days in the heatmap calendar.
        """

        driver = self._driver
        driver.get('{}/heatmap'.format(self._visualization_url))

        year = self._wait_for(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'days')))
        days = year.find_elements_by_class_name('day-group')
        self.assertEqual(len(days), 365)
        day = days[101]
        hover = ActionChains(driver)
        hover.move_to_element_with_offset(day, 1, 1).click().perform()

        tooltip = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'tooltip')))
        self.assertIn("April 12, 2018", tooltip.find_element_by_tag_name('h3').text)

    def test_leaderboard(self):
        """
        Test the Leaderboard visualization.
        """

        driver = self._driver
        driver.get('{}/leaderboard'.format(self._visualization_url))
        self.assertIn("Leaderboard", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 1)

    def test_process_flow(self):
        """
        Test the Process flow visualization.
        """

        driver = self._driver
        driver.get('{}/process-flow'.format(self._visualization_url))
        self.assertIn("Process flow", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 1)

    def test_sprint_report(self):
        """
        Test the sprint report visualization.
        """

        driver = self._driver
        driver.get('{}/sprint-report'.format(self._visualization_url))
        self.assertIn("Sprint report", driver.title)

        items = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(items.find_elements_by_tag_name('li')), 3)
        item = items.find_element_by_css_selector('li:last-child')
        item.click()

        table = self._wait_for(expected_conditions.visibility_of_element_located((By.TAG_NAME, 'table')))
        self.assertEqual(len(table.find_elements_by_tag_name('tbody')), 1)
        project = table.find_element_by_class_name('project')
        self.assertEqual(len(project.find_elements_by_class_name('sprint')), 1)
        self.assertEqual(project.find_element_by_class_name('board').text, 'Proj1')
        self.assertEqual(project.find_element_by_class_name('display-name').text, 'Project1')
        self.assertEqual(len(table.find_elements_by_class_name('feature')), 3)

        formats = driver.find_element_by_id('format')
        old_display = table
        for item in formats.find_elements_by_css_selector('li:not(:first-child)'):
            item.click()

            self._wait_for(expected_conditions.staleness_of(old_display))
            chart = self._wait_for(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'chart')))
            self.assertEqual(len(chart.find_elements_by_class_name('feature')), 3)
            old_display = chart

    def test_sprint_report_export(self):
        """
        Test the export mechanism of the sprint report visualization.
        """

        driver = self._driver
        driver.get('{}/sprint-report'.format(self._visualization_url))

        icon = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'a[data-toggle=export]')))
        icon.click()

        export = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'export')))
        exports = {
            'csv': SprintReportExportFilename(driver, {
                'filename': 'sprint-report.csv'
            }),
            'html': SprintReportExportFilename(driver, {
                'filename': 'sprint-report.zip'
            }),
            'link': SprintReportExportAttribute(driver, 'data-tooltip',
                                                'Copied link to the clipboard')
        }
        for exporter, test_case in exports.items():
            button = export.find_element_by_id('export-{}'.format(exporter))
            button.click()
            self.assertTrue(test_case.test(button),
                            test_case.get_message(exporter))

    def test_timeline(self):
        """
        Test the Timeline visualization.
        """

        driver = self._driver
        driver.get('{}/timeline'.format(self._visualization_url))
        self.assertIn("Timeline", driver.title)

        labels = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#chart-holder svg .labels')))
        self.assertEqual(len(labels.find_elements_by_tag_name('text')), 1)

        weekday = driver.find_element_by_css_selector('[data-weekday-scale]')
        weekday.click()

        self._wait_for(expected_conditions.staleness_of(labels))

        sprint = driver.find_element_by_id('line-drop-0-0')
        hover = ActionChains(driver)
        hover.move_to_element_with_offset(sprint, 1, 1).perform()

        tooltip = self._wait_for(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'tooltip')))
        self.assertIn("Start", tooltip.find_element_by_tag_name('h3').text)

        hover = ActionChains(driver)
        hover.move_to_element_with_offset(sprint, 1, 1).click().perform()

        burndown = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#subchart-holder .burndown-chart')))
        self.assertEqual(len(burndown.find_elements_by_tag_name('circle')), 6)

    def test_navbar(self):
        """
        Test whether the navbar is functional.
        """

        driver = self._driver
        driver.get(self._visualization_url)
        container = driver.find_element_by_id('navbar')
        fullscreen = container.find_element_by_class_name('navbar-fullscreen')
        fullscreen.click()
        self.assertEqual(driver.get_window_position(), {'x': 0, 'y': 0})

    def tearDown(self):
        if self._driver is not None:
            self._driver.save_screenshot('results/{}.png'.format(self.id()))
            self._results_index.write('<li><a href="{0}.png">{0}</a></li>'.format(self.id()))

            for entry in self._driver.get_log('browser'):
                print(entry)

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

            self._driver.close()

    @classmethod
    def tearDownClass(cls):
        cls._results_index.write('</ul>')
        cls._results_index.close()

        response = urlopen('http://coverage.test:8888/download')
        with closing(response):
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
