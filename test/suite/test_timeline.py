"""
Tests for the Timeline visualization.
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
        driver.get('{}/timeline'.format(self._visualization_url))
        self.assertIn("Timeline", driver.title)

        labels = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#chart-holder svg .labels')))
        self.assertEqual(len(labels.find_elements_by_tag_name('text')), 1)

        # Test the weekday scale selector.
        weekday = driver.find_element_by_css_selector('[data-weekday-scale]')
        weekday.click()

        self._wait_for(expected_conditions.staleness_of(labels))

    @skip_unless_visualization("timeline")
    def test_timeline_sprint(self):
        """
        Test the tooltip and subchart for sprints in the Timeline visualization.
        """

        driver = self._driver
        driver.get('{}/timeline'.format(self._visualization_url))
        x_axis = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#chart-holder svg .x-axis')))
        sprint = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'line-drop-0-0')))
        zoom_out = driver.find_element_by_css_selector('[data-zoom="-1"]')
        zooms = 0
        while zooms < 5 and sprint.location['x'] < x_axis.location['x']:
            zoom_out.click()
            time.sleep(1)
            zooms += 1

        hover = ActionChains(driver)
        hover.move_to_element_with_offset(sprint, 1, 1).perform()

        tooltip = self._wait_for(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'tooltip')))
        self.assertIn("Start", tooltip.find_element_by_tag_name('h3').text)

        hover = ActionChains(driver)
        hover.move_to_element_with_offset(sprint, 1, 1).click().perform()

        burndown = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#subchart-holder .burndown-chart')))
        self.assertEqual(len(burndown.find_elements_by_tag_name('circle')), 6)
