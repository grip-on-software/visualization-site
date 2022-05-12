"""
Tests for the BigBoat status visualization.

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

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from .base import IntegrationTest, skip_unless_visualization

class BigboatStatusTest(IntegrationTest):
    """
    Integration tests for the BigBoat status visualization.
    """

    @skip_unless_visualization("bigboat-status")
    def test_bigboat_status(self):
        """
        Test the BigBoat status visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/bigboat-status')
        self.assertIn("BigBoat status", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'content')
        ))
        self.assertIn("TEST", element.find_element_by_tag_name('h2').text)
        self.assertEqual("http://www.dashboard.test/",
            element.find_element_by_id('source-url').get_attribute('href')
        )
        self.assertIn("2017-06-27 09:00:39",
                      element.find_element_by_id('last-checked').text)

        graph = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'average-reliability')
        ))
        ActionChains(driver).move_to_element_with_offset(graph, 480, 250).click().perform()

        focus = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#average-reliability .focus')
        ))
        tspan = self._wait_for(expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, '#average-reliability .focus tspan')
        ))
        self.assertEqual(tspan.text, '26 Jun 18:31')
        self.assertEqual(focus.find_element_by_css_selector('tspan:last-child').text,
                         'Available IPs')
        self.assertEqual(focus.get_attribute('transform'), 'translate(568,450)')
