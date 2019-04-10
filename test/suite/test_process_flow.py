"""
Tests for the Process Flow visualization.
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
        driver.get('{}/process-flow'.format(self._visualization_url))
        self.assertIn("Process Flow", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 1)

        self._wait_for(expected_conditions.text_to_be_present_in_element((By.CSS_SELECTOR, '#slider output'), '5'))

        graph = self._wait_for(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'graph')))
        self.assertEqual(len(graph.find_elements_by_class_name('node')), 7)
        # There is a total of 12 links but two (Open -> Resolved Won't Fix and
        # Open -> Closed Redundant) are not shown by default.
        self.assertEqual(len(graph.find_elements_by_class_name('edge')), 10)
