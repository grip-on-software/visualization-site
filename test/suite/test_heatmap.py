"""
Tests for the Heatmap visualization.

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

class HeatmapTest(IntegrationTest):
    """
    Integration tests for the Heatmap visualization.
    """

    @skip_unless_visualization("heatmap")
    def test_heatmap(self):
        """
        Test the Heatmap visualization.
        """

        driver = self._driver
        driver.get('{}/heatmap'.format(self._visualization_url))
        self.assertIn("Heatmap", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'projectPicker')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 2)

    @skip_unless_visualization("heatmap")
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
