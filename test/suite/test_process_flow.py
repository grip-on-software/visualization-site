"""
Tests for the Process Flow visualization.

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

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from .base import IntegrationTest, skip_unless_visualization

class ProcessFlowTest(IntegrationTest):
    """
    Integration tests for the Process flow visualization.
    """

    @skip_unless_visualization("process-flow")
    def test_process_flow(self):
        """
        Test the Process flow visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/process-flow')
        self.assertIn("Process Flow", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.ID, 'navigation')
        ))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 1)

        self._wait_for(expected_conditions.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#slider output'), '5'
        ))

        graph = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CLASS_NAME, 'graph')
        ))
        self.assertEqual(len(graph.find_elements_by_class_name('node')), 7)
        # There is a total of 12 links but two (Open -> Resolved Won't Fix and
        # Open -> Closed Redundant) are not shown by default.
        self.assertEqual(len(graph.find_elements_by_class_name('edge')), 10)
