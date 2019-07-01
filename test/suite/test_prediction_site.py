"""
Tests for the prediction site.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from .base import IntegrationTest, skip_unless_visualization

class PredictionSiteTest(IntegrationTest):
    """
    Integration tests for the Prediction site.
    """

    @skip_unless_visualization("prediction-site")
    def test_prediction_site(self):
        """
        Test the prediction site.
        """

        driver = self._driver
        driver.get(self._prediction_url)
        self.assertIn("Prediction", driver.title)
        navigation = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(navigation.find_elements_by_tag_name('li')), 1)

        driver.get("{}/show/TEST/".format(self._prediction_url))
        title = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'project')))
        self.assertEqual(title.text, "Test")
