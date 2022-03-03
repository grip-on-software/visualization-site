"""
Report handler for the test suite.
"""

from collections import OrderedDict
from contextlib import closing
from datetime import datetime
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

class Reporter:
    """
    Report handler for results and accessibility.
    """

    _browser_logs = OrderedDict()

    @classmethod
    def setup(cls):
        """
        Set up the reports.
        """

        cls._results_index = open('results/index.html', 'w')
        cls._results_index.write('<!doctype html><html><head>')
        cls._results_index.write('<meta charset="utf-8">')
        cls._results_index.write('<title>Visualization test results</title>')
        cls._results_index.write('</head><body><h1>Test results</h1>')
        cls._results_index.write('<p>Started: {0}</p>'.format(datetime.now()))
        cls._results_index.write('<h2>Browser screenshots</h2><ul>')

        cls._accessibility_index = open('accessibility/index.html', 'w')
        cls._accessibility_index.write('<!doctype html><html><head>')
        cls._accessibility_index.write('<meta charset="utf-8">')
        cls._accessibility_index.write('<title>Accessibility results</title>')
        cls._accessibility_index.write('</head><body><h1>Accessibility</h1>')

    @classmethod
    def write_result(cls, name):
        """
        Write a link to a screenshot of a test result to the index.

        The `name` is the name of the test for which the screenshot was made.
        """

        cls._results_index.write('<li><a href="{0}.png">{0}</a></li>'.format(name))

    @classmethod
    def write_log(cls, name, log):
        """
        Write a file with a browser log of a test result.
        """

        with open('results/{0}.html'.format(name), 'w') as results_log:
            results_log.write('<!doctype html><html><head>')
            results_log.write('<meta charset="utf-8">')
            results_log.write('<link rel="stylesheet" type="text/css" href="log.css">')
            results_log.write('<title>Browser logs for {0}</title>'.format(name))
            results_log.write('</head><body><h1>Browser logs for {0}</h1>'.format(name))
            results_log.write('<table><thead><tr><th>Timestamp</th><th>Level</th><th>Source</th><th>Message</th></tr></thead><tbody>')

            for line in log:
                try:
                    timestamp = datetime.fromtimestamp(line['timestamp'] / 1000)
                except ValueError:
                    timestamp = line['timestamp']
                results_log.write('<tr><td>{0}</td><td>{level}</td><td>{source}</td><td>{message}</td></tr>'.format(timestamp, **line))

            results_log.write('</tbody></table></body></html>')

        cls._browser_logs[name] = len(log)

    @classmethod
    def write_accessibility(cls, name, report):
        """
        Write an accessibility report of a test result to the index.
        """

        section = '<h2>{0}</h2><pre>{1}</pre>'.format(name, report)
        cls._accessibility_index.write(section)

    @classmethod
    def close(cls):
        """
        Close the reports.
        """

        with open('results/log.css', 'w') as log_stylesheet:
            log_stylesheet.write('table,th,td{border:.1rem solid #aaa;border-collapse:collapse}')

        cls._results_index.write('</ul><h2>Browser logs</h2><ul>')
        for name, size in cls._browser_logs.items():
            cls._results_index.write('<li><a href="{0}.html">{0} ({1} lines)</a></li>'.format(name, size))

        # Docker container logs are appended to the index by run-tests.sh
        # Do not close the HTML here
        cls._results_index.write('</ul>')
        cls._results_index.close()

        cls._accessibility_index.write('</body></html>')
        cls._accessibility_index.close()

        zip_response = urlopen('http://coverage.test:8888/download')
        with closing(zip_response):
            if zip_response.getcode() != 200:
                print('No coverage HTML report downloaded!')
                print('\n'.join(zip_response))
            else:
                with BytesIO(zip_response.read()) as zip_data:
                    with ZipFile(zip_data, 'r') as zip_file:
                        zip_file.extractall('coverage/')

        json_response = urlopen('http://coverage.test:8888/object')
        with closing(json_response):
            if json_response.getcode() != 200:
                print('No coverage JSON data downloaded!')
                print('\n'.join(json_response))
            else:
                with open('coverage/output/out.json', 'wb') as json_file:
                    json_file.write(json_response.read())
