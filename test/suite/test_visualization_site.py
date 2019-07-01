"""
Tests for the visualization site.
"""

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

        driver.get('http://{}'.format(self._config['www_server']))
        self.assertIn("Visualizations from GROS", driver.title)

        if 'blog_url' in self._config and self._config['blog_url']:
            driver.get(self._config['blog_url'])
            self.assertIn("GROS project update", driver.title)

        if 'discussion_url' in self._config and self._config['discussion_url']:
            driver.get(self._config['discussion_url'])
            self.assertIn("GROS Discussion", driver.title)

        driver.get("{}/foobar".format(self._prediction_url))
        self.assertIn("Not found", driver.title)

    def test_navbar(self):
        """
        Test whether the navbar is functional.
        """

        driver = self._driver
        driver.get(self._visualization_url)
        container = driver.find_element_by_id('navbar')
        fullscreen = container.find_element_by_class_name('navbar-fullscreen')
        fullscreen.click()
        self.assertEqual(driver.get_window_position(), {'x': 0, 'y': 0})
