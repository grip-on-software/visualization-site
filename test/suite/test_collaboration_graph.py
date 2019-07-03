"""
Tests for the Collaboration Graph visualization.
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
        driver.get('{}/collaboration-graph'.format(self._visualization_url))
        self.assertIn("Collaboration Graph", driver.title)

        links = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'svg#graph .links')))
        self.assertEqual(len(links.find_elements_by_tag_name('line')), 3)
        nodes = driver.find_element_by_css_selector('svg#graph .nodes')
        self.assertEqual(len(nodes.find_elements_by_tag_name('circle')), 5)

    @skip_unless_visualization("collaboration-graph")
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

    @skip_unless_visualization("collaboration-graph")
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

        time.sleep(5)
        self.assertEqual(circles[2].get_attribute('fill'), 'red')

    @skip_unless_visualization("collaboration-graph")
    def test_collaboration_graph_timelapse(self):
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