"""
Tests for the Timeline visualization.

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

import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from .base import IntegrationTest, skip_unless_visualization

class TimelineTest(IntegrationTest):
    """
    Integration tests for the Timeline visualization.
    """

    @skip_unless_visualization("timeline")
    def test_timeline(self):
        """
        Test the Timeline visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/timeline')
        self.assertIn("Timeline", driver.title)

        labels = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#chart-holder svg .labels')
        ))
        self.assertEqual(len(labels.find_elements(By.TAG_NAME, 'text')), 1)

        # Test the weekday scale selector.
        weekday = driver.find_element(By.CSS_SELECTOR, '[data-weekday-scale]')
        weekday.click()

        self._wait_for(expected_conditions.staleness_of(labels))

    @skip_unless_visualization("timeline")
    def test_timeline_sprint(self):
        """
        Test the tooltip and subchart for sprints in the Timeline visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/timeline')
        x_axis = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#chart-holder svg .x-axis')
        ))
        sprint = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'line-drop-0-0')
        ))
        zoom_out = driver.find_element(By.CSS_SELECTOR, '[data-zoom="-1"]')
        zooms = 0
        while zooms < 5 and sprint.location['x'] < x_axis.location['x']:
            zoom_out.click()
            time.sleep(1)
            zooms += 1

        ActionChains(driver).move_to_element(sprint).perform()

        tooltip = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CLASS_NAME, 'tooltip')
        ))
        self.assertIn("Start", tooltip.find_element(By.TAG_NAME, 'h3').text)

        ActionChains(driver).move_to_element(sprint).click().perform()

        burndown = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#subchart-holder .burndown-chart')
        ))
        self._wait_for(expected_conditions.staleness_of(tooltip))
        self.assertEqual(len(burndown.find_elements(By.TAG_NAME, 'circle')), 6)
