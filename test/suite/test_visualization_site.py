"""
Tests for the visualization site.

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
from .base import IntegrationTest

class VisualizationSiteTest(IntegrationTest):
    """
    Integration tests for the main visualization site and related pages.
    """

    def test_reachability(self):
        """
        Test whether the hubs are reachable and serve correct pages.
        """

        driver = self._driver
        driver.get(self._visualization_url)
        self.assertIn("Visualizations from GROS", driver.title)

        driver.get(f'http://{self._config["www_server"]}')
        self.assertIn("Visualizations from GROS", driver.title)

        if 'blog_url' in self._config and self._config['blog_url']:
            driver.get(self._config['blog_url'])
            self.assertIn("GROS project update", driver.title)

        if 'discussion_url' in self._config and self._config['discussion_url']:
            driver.get(self._config['discussion_url'])
            self.assertIn("GROS Discussion", driver.title)

        driver.get(f"{self._prediction_url}/foobar")
        self.assertIn("Not found", driver.title)

    def test_navbar(self):
        """
        Test whether the navbar is functional.
        """

        driver = self._driver
        driver.get(self._visualization_url)
        container = driver.find_element(By.ID, 'navbar')
        fullscreen = container.find_element(By.CLASS_NAME, 'navbar-fullscreen')
        fullscreen.click()
        self.assertEqual(driver.get_window_position(), {'x': 0, 'y': 0})
