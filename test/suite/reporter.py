"""
Report handler for the test suite.

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

from collections import OrderedDict
from contextlib import closing
from datetime import datetime
from io import BytesIO
import os
from urllib.error import URLError
from urllib.request import urlopen
from zipfile import ZipFile

class Reporter:
    """
    Report handler for results and accessibility.
    """

    def __init__(self):
        """
        Set up the reports.
        """

        self._results_index = None
        self._accessibility_index = None
        self._browser_logs = OrderedDict()

    def __enter__(self):
        build_url = os.getenv('BUILD_URL', '')
        build_id = os.getenv('BUILD_NUMBER', '')
        configuration = [
            ['Build', f'<a href="{build_url}">{build_id}</a>'],
            ['Started', datetime.now().astimezone()],
            ['Branch', os.getenv('BRANCH_NAME', '')],
            ['Host node', os.getenv('NODE_NAME', '')],
            ['Main organization', os.getenv('VISUALIZATION_ORGANIZATION', '')],
            ['Combined', os.getenv('VISUALIZATION_COMBINED', 'false')]
        ]
        self._results_index = open('results/index.html', 'w', encoding='utf-8')
        self._results_index.write('<!doctype html>\n<html>\n<head>\n')
        self._results_index.write('<meta charset="utf-8">\n')
        self._results_index.write('<title>Visualization tests</title>\n')
        self._results_index.write('</head>\n<body>\n<h1>Test results</h1>\n')
        self._results_index.write('<h2>Configuration</h2>\n<dl>\n')
        self._results_index.write('\n'.join(
            f'<dt>{name}</dt>\n<dd>{value}</dd>\n'
            for name, value in configuration
        ))
        self._results_index.write('</dl>\n<h2>Browser screenshots</h2>\n<ul>\n')

        self._accessibility_index = open('accessibility/index.html', 'w',
                                         encoding='utf-8')
        self._accessibility_index.write('<!doctype html>\n<html>\n<head>\n')
        self._accessibility_index.write('<meta charset="utf-8">\n')
        self._accessibility_index.write('<title>Accessibility tests</title>\n')
        self._accessibility_index.write('</head>\n<body>\n')
        self._accessibility_index.write('<h1>Accessibility test results</h1>\n')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write_result(self, name):
        """
        Write a link to a screenshot of a test result to the index.

        The `name` is the name of the test for which the screenshot was made.
        """

        self._results_index.write(f'<li><a href="{name}.png">{name}</a></li>\n')

    def write_log(self, name, log):
        """
        Write a file with a browser log of a test result.
        """

        with open(f'results/{name}.html', 'w', encoding='utf-8') as results_log:
            results_log.write('<!doctype html>\n<html>\n<head>\n')
            results_log.write('<meta charset="utf-8">\n')
            results_log.write('<link rel="stylesheet" type="text/css" href="log.css">\n')
            results_log.write(f'<title>Browser logs for {name}</title>\n')
            results_log.write('</head>\n<body>\n')
            results_log.write(f'<h1>Browser logs for {name}</h1>')
            results_log.write("""
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Level</th>
                            <th>Source</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody>""")

            for line in log:
                try:
                    timestamp = datetime.fromtimestamp(line['timestamp'] / 1000)
                except ValueError:
                    timestamp = line['timestamp']
                results_log.write(f"""
                        <tr>
                            <td>{timestamp}</td>
                            <td>{line['level']}</td>
                            <td>{line['source']}</td>
                            <td>{line['message']}</td>
                        </tr>""")
                comment_line = repr(line).replace('--', '\u2014')
                results_log.write(f"<!-- {comment_line} -->\n")

            results_log.write('</tbody>\n</table>\n')
            results_log.write(f'<p>Finished: {datetime.now().astimezone()}</p>')
            results_log.write('\n</body>\n</html>')

        self._browser_logs[name] = len(log)

    def write_accessibility(self, name, report):
        """
        Write an accessibility report of a test result to the index.
        """

        self._accessibility_index.write(f'<h2>{name}</h2>\n')
        self._accessibility_index.write(f'<pre>{report}</pre>\n')

    def close(self):
        """
        Close the reports.
        """

        with open('results/log.css', 'w', encoding='utf-8') as log_stylesheet:
            log_stylesheet.write("""
table,th,td {
    border: .1rem solid #aaa;
    border-collapse: collapse
}
dt {
    font-weight: bold
}""")

        self._results_index.write('</ul>\n<h2>Browser logs</h2>\n<ul>\n')
        for name, size in self._browser_logs.items():
            self._results_index.write(f'<li><a href="{name}.html">{name} ({size} lines)</a></li>\n')

        # Docker container logs are appended to the index by run-tests.sh
        # Do not close the HTML here
        self._results_index.write('</ul>\n')
        self._results_index.close()

        self._accessibility_index.write('</body>\n</html>')
        self._accessibility_index.close()

        coverage_url = 'http://coverage.test:8888'

        try:
            with closing(urlopen(f'{coverage_url}/download')) as zip_response:
                if zip_response.getcode() != 200:
                    print('No coverage HTML report downloaded!')
                    print('\n'.join(zip_response))
                else:
                    with BytesIO(zip_response.read()) as zip_data:
                        with ZipFile(zip_data, 'r') as zip_file:
                            zip_file.extractall('coverage/')

            with closing(urlopen(f'{coverage_url}/object')) as json_response:
                if json_response.getcode() != 200:
                    print('No coverage JSON data downloaded!')
                    print('\n'.join(json_response))
                else:
                    with open('coverage/output/out.json', 'wb') as json_file:
                        json_file.write(json_response.read())
        except URLError as error:
            print(f'Could not collect coverage data from {coverage_url}: {error}')
