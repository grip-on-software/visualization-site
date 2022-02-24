"""
Report handler for the test suite.
"""

from contextlib import closing
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

class Reporter:
    """
    Report handler for results and accessibility.
    """

    @classmethod
    def setup(cls):
        """
        Set up the reports.
        """

        cls._results_index = open('results/index.html', 'w')
        cls._results_index.write('<!doctype html><html><head>')
        cls._results_index.write('<meta charset="utf-8">')
        cls._results_index.write('<title>Visualization test results</title>')
        cls._results_index.write('</head><body><h1>Test results</h1><ul>')

        cls._accessibility_index = open('accessibility/index.html', 'w')
        cls._accessibility_index.write('<!doctype html><html><head>')
        cls._accessibility_index.write('<meta charset="utf-8">')
        cls._accessibility_index.write('<title>Accessibility results</title>')
        cls._accessibility_index.write('</head><body><h1>Accessibility</h1>')

    @classmethod
    def write_result(cls, name):
        """
        Write a results name to the index.
        """

        cls._results_index.write('<li><a href="{0}.png">{0}</a></li>'.format(name))

    @classmethod
    def write_accessibility(cls, name, report):
        """
        Write an accessibility report to the index.
        """

        section = '<h2>{0}</h2><pre>{1}</pre>'.format(name, report)
        cls._accessibility_index.write(section)

    @classmethod
    def close(cls):
        """
        Close the reports.
        """

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
