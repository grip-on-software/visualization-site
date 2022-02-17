# GROS visualization proxy and site

This repository contains configuration files and static web files for the 
visualization hub of the GROS project. The proxy is intended to provide access 
to a Ghost blog and Discourse forum if they are deployed within the 
environment, as well as to the visualization reports for the organization, 
which were generated using branch-based builds on a Jenkins instance.

The repository needs to be configured to work within a specific environment. 
Two stages of reverse proxies are used to safely provide access to the GROS 
webservers (separate Docker instances, a Jenkins setup and/or direct access). 
The reverse proxies are as follows:

- [Caddy](https://caddyserver.com/) for transparent proxy access from a BigBoat 
  dashboard. Several subinstances handle specific domain names.
- [NGINX](https://www.nginx.com/) for proxy access and static file hosting from 
  a central server listening on specific ports as well as using Host-based 
  proxying.

Additionally, this repository contains a Shell script `goaccess-report.sh` that 
can be run periodically to generate a server statistics report. It requires 
installation of [GoAccess](https://goaccess.io/) which analyzes logs and 
creates an analytics dashboard.

Separate documentation exists for more details on how the second proxy layer 
works.

## Tests

This repository contains integration tests for the visualizations. The entire 
visualization proxy layer setup is emulated within a `docker-compose` network, 
with each deployed visualization within its own Docker instance running its 
Node.js development web service. A Caddy proxy pretends to be the Jenkins 
server with access to the HTML reports and artifacts.

The tests themselves are run with a Selenium instance using a Chromium browser, 
which is being controlled by a Python runner. The tests are in the form of 
Python unit tests which instruct the Selenium instance to navigate to pages and 
perform actions such as clicking. The unit tests then check if certain elements 
are visible, contain certain text, or have other properties, and the test 
passes if this is the case.

The visualizations use their test builds which contain coverage tracking, which 
is extracted and combined after the test completes. In addition to coverage, 
Sonar scans check for code smells, and a dependency check searches for 
vulnerabilities.

At the end of each test, more actions take place. Logs are stored and 
a screenshot is made of the page, so that there is a visual reference of the 
state of the page in case a test fails. Finally, an accessibility testing 
engine is used to verify if the contents of the page conform to various WCAG 
rules. All of these results are combined as well into a report.
