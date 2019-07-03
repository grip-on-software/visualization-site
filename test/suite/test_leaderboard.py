"""
Tests for the Leaderboard visualization.
"""

from collections import OrderedDict
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from .base import IntegrationTest, skip_unless_visualization

class LeaderboardTest(IntegrationTest):
    """
    Integration tests for the Leaderboard visualization.
    """

    @skip_unless_visualization("leaderboard")
    def test_leaderboard(self):
        """
        Test the Leaderboard visualization.
        """

        driver = self._driver
        driver.get('{}/leaderboard'.format(self._visualization_url))
        self.assertIn("Leaderboard", driver.title)

        element = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'navigation')))
        self.assertEqual(len(element.find_elements_by_tag_name('li')), 1)

    @skip_unless_visualization("leaderboard")
    def test_leaderboard_sort(self):
        """
        Test the sort mechanism of the Leaderboard visualization.
        """

        driver = self._driver
        driver.get('{}/leaderboard'.format(self._visualization_url))

        cards = self._wait_for(expected_conditions.visibility_of_element_located((By.ID, 'cards')))
        self.assertEqual(len(cards.find_elements_by_class_name('card')), 15)

        num_sprints = 9.
        num_repos = 4.
        num_issues = 932.
        num_commits = 999.
        features = OrderedDict([
            ("Issues", ("jira", num_issues / num_sprints)),
            ("Stories", ("jira", 278 / num_sprints)),
            ("Comments", ("jira", 2215 / num_sprints)),
            ("Test Cases", ("jira", 166)),
            ("Repositories", ("vcs", num_repos)),
            ("Commit Tags", ("vcs", 137 / num_repos)),
            ("Issue Links", ("jira", 311 / num_issues)),
            ("Commits", ("vcs", num_commits / num_sprints)),
            ("Commit Pushes", ("vcs", 1200 / num_sprints)),
            ("Merges", ("vcs", 233 / num_commits)),
            ("Merge Requests", ("vcs", 11)),
            ("Sprints", (("jira", "normalize"), num_sprints)),
            ("Life Span", (("jira", "normalize"), 723)),
            ("Fix Versions", ("jira", 5 / num_sprints)),
            ("Build Jobs", ("jenkins", 2))
        ])
        titles = lambda cards: [title.text for title in cards.find_elements_by_class_name('card-title')]

        self.assertEqual(titles(cards), list(features.keys()))

        driver.find_element_by_css_selector('.radio input[value="feature"]').click()
        self.assertEqual(titles(cards), list(sorted(features.keys())))

        driver.find_element_by_css_selector('.radio input[value="group"]').click()

        group_sort = lambda name: (len(features[name][0]), features[name][0]) \
            if isinstance(features[name][0], tuple) else (1, (features[name][0],))
        self.assertEqual(titles(cards),
                         list(sorted(features.keys(),
                                     key=lambda name: (group_sort(name), name))))

        driver.find_element_by_css_selector('.radio input[value="score"]').click()
        self.assertEqual(titles(cards),
                         list(sorted(features.keys(),
                                     key=lambda name: features[name][1])))

        icon = cards.find_element_by_css_selector('a.card-header-icon')
        icon.click()

        self._wait_for(expected_conditions.staleness_of(icon))
        self._wait_for(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '.radio input[value="project"]'))).click()
        card = self._wait_for(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'card')))
        self.assertEqual(card.find_element_by_class_name('ellipsized-title').text, 'P1')