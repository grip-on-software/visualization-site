"""
Tests for the Sprint Report visualization.

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

from pathlib import Path
import unittest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from .base import IntegrationTest, skip_unless_visualization

class SprintReportFormatTest:
    """
    Test case for a sprint report format mechanism.
    """

    def get_test_element_locator(self):
        """
        Get the Selenium locator tuple to find an element that is created
        after selecting the format.
        """

        raise NotImplementedError('Must be implemented by subclasses')

    def test(self, runner, element):
        """
        Perform unit tests upon the located element.
        """

        raise NotImplementedError('Must be implemented by subclasses')

class SprintReportFormatTable(SprintReportFormatTest):
    """
    Test case for the table format.
    """

    def get_test_element_locator(self):
        return (By.CSS_SELECTOR, '#format-content table')

    def test(self, runner, element):
        runner.assertEqual(len(element.find_elements(By.TAG_NAME, 'tbody')), 1)
        project = element.find_element(By.CLASS_NAME, 'project')
        runner.assertEqual(len(project.find_elements(By.CLASS_NAME, 'sprint')),
                           1)
        runner.assertEqual(project.find_element(By.CLASS_NAME, 'board').text,
                           'Proj1')
        runner.assertEqual(project.find_element(By.CLASS_NAME,
                                                'display-name').text,
                           'Project1')
        runner.assertEqual(len(element.find_elements(By.CLASS_NAME, 'feature')),
                           3)

class SprintReportFormatChart(SprintReportFormatTest):
    """
    Test case for chart formats.
    """

    def __init__(self, selectors):
        super().__init__()
        self.selectors = selectors

    def get_test_element_locator(self):
        return (By.CLASS_NAME, 'chart')

    def test(self, runner, element):
        for selector, count in self.selectors:
            runner.assertEqual(len(element.find_elements(By.CSS_SELECTOR,
                                                         selector)), count)

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
        super().__init__(driver)
        self.options = {
            'filename': 'sprint-report',
            'path': '/work/downloads',
            'timeout': 5,
            'poll_frequency': 0.5
        }
        self.options.update(options)

    def test(self, button):
        path = Path(self.options['path']) / self.options['filename']
        wait = WebDriverWait(self._driver, self.options['timeout'],
                             self.options['poll_frequency'])
        try:
            wait.until(lambda driver: path.exists())
        except TimeoutException:
            return False

        return True

    def get_message(self, exporter):
        return (
            f'{self.options["path"]}/{self.options["filename"]} exists within'
            f'{self.options["timeout"]} seconds after {exporter} export'
        )

class SprintReportExportAttribute(SprintReportExportTest):
    """
    Test case for a sprint report export attribute change.
    """

    def __init__(self, driver, attribute, value):
        super().__init__(driver)
        self.attribute = attribute
        self.value = value

    def test(self, button):
        return button.get_attribute(self.attribute) == self.value

    def get_message(self, exporter):
        return f'{exporter} export has attribute {self.attribute}={self.value}'

class SprintReportTest(IntegrationTest):
    """
    Integration tests for the sprint report visualization.
    """

    @skip_unless_visualization("sprint-report")
    def test_sprint_report(self):
        """
        Test the sprint report visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/sprint-report')
        self.assertIn("Sprint report", driver.title)

        # Select one project
        items = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'navigation')
        ))
        self.assertEqual(len(items.find_elements(By.TAG_NAME, 'li')), 3)
        item = items.find_element(By.CSS_SELECTOR, 'li:last-child')
        item.click()

        # Format options
        options = driver.find_element(By.ID, 'format')
        formats = {
            'table': SprintReportFormatTable(),
            'line_chart': SprintReportFormatChart([
                ('.features.lines .feature', 3)
            ]),
            'bar_chart': SprintReportFormatChart([
                ('.features .feature', 3)
            ]),
            'area_chart': SprintReportFormatChart([
                ('.features.areas .feature', 3),
                ('.features.lines .feature', 3)
            ]),
            'scatter_plot': SprintReportFormatChart([
                ('.features circle', 1)
            ]),
            'sankey_chart': SprintReportFormatChart([
                ('g.nodes g', 3)
            ])
        }
        old_display = None
        for name, formatter in formats.items():
            item = options.find_element(By.ID, f'format-{name}')
            item.click()

            if old_display is not None:
                self._wait_for(expected_conditions.staleness_of(old_display))

            element = self._wait_for(expected_conditions.visibility_of_element_located(
                formatter.get_test_element_locator()
            ))
            formatter.test(self, element)
            old_display = element

    @skip_unless_visualization("sprint-report")
    def test_sprint_report_focus(self):
        """
        Test the focus tooltip of a chart format in the sprint report
        visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/sprint-report')

        # Select one project
        items = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'navigation')
        ))
        item = items.find_element(By.CSS_SELECTOR, 'li:last-child')
        item.click()

        # Format option: Line chart
        item = driver.find_element(By.ID, 'format-line_chart')
        item.click()

        chart = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CLASS_NAME, 'chart')
        ))
        # Move cursor into chart, wait until the chart is fully loaded, then
        # move to a location where we can get a focus element. Move again and
        # see if the focus properly becomes loaded.
        hover = ActionChains(driver)
        hover.move_to_element(chart).pause(0.5).scroll_to_element(chart)
        hover.move_to_element_with_offset(chart, -280, 0).pause(0.5)
        hover.move_to_element_with_offset(chart, 0, 0).click()
        hover.perform()

        focus = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CLASS_NAME, 'focus')
        ))
        details = focus.find_elements(By.TAG_NAME, 'tspan')
        # 3 sprint metadata (name, number, close date) + 3 features with
        # 3 tspan elements each (wrapper, feature name, value)
        self.assertEqual(len(details), 12)

    @skip_unless_visualization("sprint-report")
    def test_sprint_report_source_age(self):
        """
        Test the source age of the sprint report visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/sprint-report')

        # Select one project
        items = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'navigation')
        ))
        self.assertEqual(len(items.find_elements(By.TAG_NAME, 'li')), 3)
        item = items.find_element(By.CSS_SELECTOR, 'li:last-child')
        item.click()

        icon = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, 'a[data-toggle=sources]')
        ))
        icon.click()

        project = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#sources th.project')
        ))
        self.assertEqual(project.text, 'Proj1')
        sources = driver.find_elements(By.CSS_SELECTOR, '#sources tbody tr')
        self.assertEqual(len(sources), 5)

    @skip_unless_visualization("sprint-report")
    def test_sprint_report_details(self):
        """
        Test the details subtable of the sprint report visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/sprint-report')
        self.assertIn("Sprint report", driver.title)

        items = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'navigation')
        ))
        self.assertEqual(len(items.find_elements(By.TAG_NAME, 'li')), 3)
        item = items.find_element(By.CSS_SELECTOR, 'li:last-child')
        item.click()

        table = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#format-content table')
        ))
        expand = table.find_element(By.CSS_SELECTOR, '.fa-expand')
        expand.click()

        details = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, 'table.details')
        ))
        rows = details.find_elements(By.CSS_SELECTOR, 'tr.detail')
        self.assertEqual(len(rows), 3)
        self.assertEqual([
            row.find_element(By.CSS_SELECTOR, 'td:first-child a').text
            for row in rows
        ], ["P1-198", "P1-224", "P1-301"])
        self.assertEqual([
            row.find_element(By.CSS_SELECTOR, 'td:last-child').text
            for row in rows
        ], ["2", "5", "0.5"])

    @skip_unless_visualization("sprint-report")
    @unittest.skip("Selenium Chromium browser is not properly downloading the files")
    def test_sprint_report_export(self):
        """
        Test the export mechanism of the sprint report visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/sprint-report')

        icon = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, 'a[data-toggle=export]')
        ))
        icon.click()

        export = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'export')
        ))
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
            button = export.find_element(By.ID, f'export-{exporter}')
            button.click()
            self.assertTrue(test_case.test(button),
                            test_case.get_message(exporter))
