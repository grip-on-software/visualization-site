"""
Test result handler.

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

from xmlrunner.result import _XMLTestResult

class Result(_XMLTestResult):
    """
    Test result that handles auxiliary result reporting.
    """

    def __init__(self, stream, descriptions, verbosity, reporter):
        super().__init__(stream, descriptions, verbosity)
        self.reporter = reporter
