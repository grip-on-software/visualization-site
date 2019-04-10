"""
Tests for the Timeline visualization.
"""

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
