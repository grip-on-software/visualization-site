"""
Tests for the prediction site.

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

class PredictionSiteTest(IntegrationTest):
    """
    Integration tests for the Prediction site.
    """

    @skip_unless_visualization("prediction-site")
    def test_prediction_site(self):
        """
        Test the prediction site index.
        """

        driver = self._driver
        driver.get(self._prediction_url)
        self.assertIn("Prediction", driver.title)

        navigation = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(navigation.find_elements_by_tag_name('li')), 3)
        recent = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#filter input')))
        recent.click()
        self.assertEqual(len(navigation.find_elements_by_tag_name('li')), 4)

        branches = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'branches-dropdown')))
        self.assertEqual(len(branches.find_elements_by_css_selector('#branches a')), 2)

        files = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'files')))
        self.assertEqual(len(files.find_elements_by_css_selector('div.card')), 2)

    @skip_unless_visualization("prediction-site")
    def test_prediction_site_project(self):
        """
        Test the prediction site for a project.
        """

        driver = self._driver
        driver.get("{}/show/TEST/".format(self._prediction_url))
        title = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'project')))
        self.assertEqual(title.text, "Test")

        sources = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#sources tbody')))
        self.assertEqual(len(sources.find_elements_by_tag_name('tr')), 5)

        features = self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '#features tbody')))
        self.assertEqual(len(features.find_elements_by_tag_name('tr')), 7)

    @skip_unless_visualization("prediction-site")
    def test_prediction_site_sprint(self):
        """
        Test the prediction site for a project with multiple sprints.
        """

        driver = self._driver
        driver.get("{}/show/P1/".format(self._prediction_url))
        title = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'project')))
        self.assertEqual(title.text, "Proj1")

        self.assertEqual(self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'sprint'))).text, '2')
        self.assertEqual(self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'name'))).text, 'Sprint 2')
        self.assertEqual(self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'prediction'))).text, '20')

        sprints = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'sprints')))
        items = sprints.find_elements_by_tag_name('li')
        self.assertEqual(len(items), 2)
        self.assertEqual(items[-1].get_attribute('class'), 'is-active')
        self.assertEqual(items[-1].find_element_by_tag_name('a').text, '#2')

        items[0].find_element_by_tag_name('a').click()
        self._wait_for(expected_conditions.staleness_of(title))
        self.assertEqual(self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'sprint'))).text, '1')
        self.assertEqual(self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'name'))).text, 'Sprint 1')
        self.assertEqual(self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'prediction'))).text, '10')

    @skip_unless_visualization('prediction-site')
    def test_prediction_site_missing(self):
        """
        Test the prediction site for a project without data.
        """

        driver = self._driver
        driver.get("{}/show/P2/?lang=nl".format(self._prediction_url))
        error = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'prediction-error-message')))
        self.assertIn("404", error.text)

        # Navigation should still be shown and honor the language parameter.
        navigation = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertIn("lang=nl", navigation.find_element_by_tag_name('a').get_attribute('href'))

    @skip_unless_visualization('prediction-site')
    def test_prediction_site_model(self):
        """
        Test the prediction site for a project with classification score.
        """

        driver = self._driver
        driver.get("{}/show/XY/".format(self._prediction_url))

        risk = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'risk')))
        self.assertEqual(risk.get_attribute('value'), '54.32')

        probability = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'probability')))
        self.assertEqual(probability.text, '85.32%')
