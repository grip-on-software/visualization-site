"""
Tests for the Collaboration Graph visualization.

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
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from .base import IntegrationTest, skip_unless_visualization

class CollaborationGraphTest(IntegrationTest):
    """
    Integration tests for the Collaboration graph visualization.
    """

    @skip_unless_visualization("collaboration-graph")
    def test_collaboration_graph(self):
        """
        Test the Collaboration graph visualization.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/collaboration-graph')
        self.assertIn("Collaboration Graph", driver.title)

        links = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, 'svg#graph .links')
        ))
        self.assertEqual(len(links.find_elements(By.TAG_NAME, 'line')), 3)
        nodes = driver.find_element(By.CSS_SELECTOR, 'svg#graph .nodes')
        self.assertEqual(len(nodes.find_elements(By.TAG_NAME, 'circle')), 5)

    @skip_unless_visualization("collaboration-graph")
    def test_collaboration_graph_extern(self):
        """
        Test the external filter mechanism of the Collaboration graph.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/collaboration-graph')

        nodes = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, 'svg#graph .nodes')
        ))
        circle = nodes.find_elements(By.TAG_NAME, 'circle')[2]

        button = driver.find_element(By.CSS_SELECTOR, '.regular-option')
        button.click()
        self._wait_for(expected_conditions.invisibility_of_element_located(circle))

        self.assertEqual(circle.get_attribute('visibility'), 'collapse')

    @skip_unless_visualization("collaboration-graph")
    def test_collaboration_graph_find(self):
        """
        Test the search mechanism of the Collaboration graph.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/collaboration-graph')

        nodes = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, 'svg#graph .nodes')
        ))
        circles = nodes.find_elements(By.TAG_NAME, 'circle')

        search = driver.find_element(By.CSS_SELECTOR, 'input.regular-option')
        search.send_keys('A')

        time.sleep(5)
        self.assertEqual(circles[2].get_attribute('fill'), 'red')

    @skip_unless_visualization("collaboration-graph")
    def test_collaboration_graph_timelapse(self):
        """
        Test the timelapse mechanism of the Collaboration graph.
        """

        driver = self._driver
        driver.get(f'{self._visualization_url}/collaboration-graph')

        button = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#options .button')
        ))
        button.click()

        self.assertEqual(len(driver.find_elements(By.CSS_SELECTOR,
                                                  '.regular-option[disabled]')),
                         2)

        buttons = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#options .buttons')
        ))
        pause = buttons.find_element(By.ID, 'pauseButton')
        slower = buttons.find_element(By.CSS_SELECTOR, '.slower')
        faster = buttons.find_element(By.CSS_SELECTOR, '.faster')

        self.assertEqual(pause.get_attribute("data-tooltip"), "Pause")
        self.assertIsNone(slower.get_attribute("disabled"))
        self.assertIsNone(faster.get_attribute("disabled"))

        faster.click()
        faster.send_keys("+")
        faster.click()

        self.assertTrue(faster.get_attribute("disabled"))

        slower.click()
        self.assertFalse(faster.get_attribute("disabled"))

        title = self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, '#options h3')
        ))
        self.assertEqual(title.text, "August 2017")

        links = driver.find_element(By.CSS_SELECTOR, 'svg#graph .links')
        self.assertEqual(len(links.find_elements(By.TAG_NAME, 'line')), 2)
        nodes = driver.find_element(By.CSS_SELECTOR, 'svg#graph .nodes')
        self.assertEqual(len(nodes.find_elements(By.TAG_NAME, 'circle')), 3)

        self._wait_for(expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, '.fa-stop')
        ))
        self.assertEqual(pause.get_attribute("data-tooltip"), "Stopped")

        button.click()
        self._wait_for(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, 'svg#graph .nodes .node:nth-child(5)')
        ))

        links = driver.find_element(By.CSS_SELECTOR, 'svg#graph .links')
        self.assertEqual(len(links.find_elements(By.TAG_NAME, 'line')), 3)
        nodes = driver.find_element(By.CSS_SELECTOR, 'svg#graph .nodes')
        self.assertEqual(len(nodes.find_elements(By.TAG_NAME, 'circle')), 5)
