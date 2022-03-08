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
  dashboard. Several subinstances handle specific domain names. This is only 
  used in an environment where access has to be routed through several VLANs.
- [NGINX](https://www.nginx.com/) for proxy access and static file hosting from 
  a central server listening on specific ports as well as using Host-based 
  proxying.

Many of the configuration files and web files use 
[Mustache](https://www.npmjs.com/package/mustache) in order to use 
configuration items and functions to adjust to other environments. 

Additionally, this repository contains a Shell script `goaccess-report.sh` that 
can be run periodically to generate a server statistics report. It requires 
installation of [GoAccess](https://goaccess.io/) which analyzes logs and 
creates an analytics dashboard.

Separate documentation exists for more details on how the second proxy layer 
works.

## Dependencies

While the build of the visualization site may work with simply having Docker 
installed, the test and production environments will need a more full-fledged 
installation of other dependencies.

For the tests, a Jenkins installation is assumed with proper OpenJDK Java 8+ 
and Python 3.6+ (including `distutils` and `virtualenv`). The agent that 
performs the tests must have `docker-compose`. In addition, tools such as Git, 
`jq`, `bash`, `awk`, `sed` and `grep` must be available. A SonarQube Scanner 
must be registered in Jenkins. The server agent that performs the publishing 
must have `curl` as well. Details for configuring Jenkins servers and agents 
are outside the scope of this documentation, although some details may be 
available in other GROS documentation.

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

## Configuration

The visualization dashboard, connections to other servers as well as common 
elements such as a navigation bar, are all configured in this repository. The 
main configuration point is the `config.json` file, which can be copied from 
`lib/config.json` to the root of the repository in order to make local 
adjustments. The following configuration items (all strings, unless noted 
otherwise) are known:

- `visualization_url`: The URL to the visualizations. This may include 
  a protocol and domain name, but does not need to in case all the resources 
  are hosted on the same domain. The remainder is a path to the root of the 
  visualizations, where the dashboard is found and every visualization (except 
  predictions) has sub-paths below it.
- `prediction_url`: The URL to the prediction site. This may include 
  a protocol and domain name, but does not need to in case all the resources 
  are hosted on the same domain. The remainder is a path to the root of the 
  predictions (without any specific paths below it).
- `blog_url`: The URL to the blog. This may include a protocol and domain name, 
  but does not need to in case all the resources are hosted on the same domain. 
  The remainder is a path to the root of the blog. If this is empty, then no 
  blog is available.
- `discussion_url`: The URL to the discussion forum. This may include 
  a protocol and domain name, but does not need to in case all the resources 
  are hosted on the same domain. The remainder is a path to the root of the 
  forum. If this is empty, then no forum is available.
- `download_url`: The URL to default download links on the dashboard. This can 
  be overwritten by specific download URLs by the visualizations and does not 
  work with the NGINX redirection, so care should be taken when adjusting this. 
  This may be helpful when direct access to downloads are available. If this is 
  empty, then no download links are shown.
- `jira_url`: URL that is used in some navigation bars to link to a Jira 
  instance.
- `blog_host`: Domain name of an internal server where the blog is hosted.
- `blog_server`: Domain name of an external server that provides access to the 
  blog. This name should point (possibly via a Caddy proxy) toward the NGINX 
  proxy that makes the server available.
- `discussion_host`: Domain name of an internal server where the discussion 
  forum is hosted.
- `discussion_server`: Domain name of an external server that provides access 
  to the discussion forum. This name should point (possibly via a Caddy proxy) 
  toward the NGINX proxy that makes the server available.
- `visualization_server`: Domain name of an external server that provides 
  access to the visualization dashboard and every visualization (except 
  predictions). This name should point (possibly via a Caddy proxy) toward the 
  NGINX proxy that makes the server available.
- `www_server`: Domain name of an external server that listens on a "www" 
  address. This server redirects to the visualization server. This name should 
  point (possibly via a Caddy proxy) toward the NGINX proxy that makes the 
  redirection service available.
- `prediction_server`: Domain name of an external server that provides access 
  to the predictions. This name should point (possibly via a Caddy proxy) 
  toward the NGINX proxy that makes the server available.
- `hub_organizations` (array): When multiple organizations are hosted in the 
  same environment, an array of objects containing organizations and branch 
  names can be used to provide a build and dummy data for visualizations on 
  multiple branches. Currently, only the `visualization-site` and 
  `prediction-site` visualizations are considered as keys in each object, and 
  they should provide a branch name that the `visualization_branch` and 
  `prediction_branch` may point to, respectively.
- `hub_regex`: When multiple organizations are hosted in the same environment, 
  a regular expression can be used to match the organization name which must 
  occur at the start of the path, and place the matched parts into variables 
  for later use in the NGINX rewrites.
- `hub_redirect`: When multiple organizations are hosted in the same 
  environment, variables from a matched organization at the start of the path 
  using `hub_regex` can be used in a rewrite that redirects to another URL. It 
  is assumed that this configuration value produces an absolute URL.
- `hub_branch`: Inject some processing steps in the NGINX configuration for the 
  visualizations hub. This should at least determine the branch of a Jenkins 
  build to use for the visualization site. When multiple organizations are 
  hosted in the same environment, variables from a matched organization at the 
  start of the path using `hub_regex` can be used in further processing.
- `visualization_branch`: Inject some processing steps in the NGINX 
  configuration for a visualization. This should at least determine the branch 
  of a Jenkins build to use for a visualization. When multiple organizations 
  are hosted in the same environment, variables from a matched organization at 
  the start of the path using `hub_regex` can be used in further processing.
- `prediction_branch`: Inject some processing steps in the NGINX configuration 
  for the prediction site. This should at least determine the branch of 
  a Jenkins build to use for the visualization or prediction site. When 
  multiple organizations are hosted in the same environment, variables from 
  a matched organization at the start of the path using `hub_regex` can be used 
  in further processing.
- `jenkins_host`: Domain name of an internal server where the Jenkins build 
  system is hosted.
- `jenkins_path`: Path that the Jenkins build system is hosted below. This is 
  useful in situations where Jenkins is hosted on the same domain as other 
  resources and is therefore within a path rather than directly at the root of 
  a domain.
- `jenkins_direct`: Filesystem path of a location where a copy of the 
  visualizations and predictions are available. If this is not empty, the 
  structure within the path must follow that which the `copy.sh` script makes 
  and supported requests are internally rewritten to this path. If this is 
  empty, then requests for visualizations and predictions are proxied to the 
  Jenkins server.
- `jenkins_direct_url`: URL through which the Jenkins server is available from 
  the location of the build (a Jenkins node with the 'publish' tag, most likely 
  the server itself), when the visualizations and predictions are copied.
- `jenkins_direct_cert`: Filesystem path to a certificate used for validating 
  a HTTPS connection to the Jenkins server, when the visualizations and 
  predictions are copied (for branch information).
- `jenkins_api_token`: Encrypted token that can be used for basic authorization 
  against the Jenkins API for at least branch details of builds.
- `files_host`: Domain name of an internal server where an ownCloud instance is 
  hosted.
- `files_share_id`: Identifier of a publish share on an ownCloud instance with 
  files that are made available in addition to the prediction resources.
- `control_host`: Domain name of an internal server where secure resources are 
  hosted, including encryption services and access control checks. This domain 
  must be accessible through HTTPS from the NGINX proxy.
- `websocket_server`: Domain name of an external server where a WebSocket for 
  real-time updates of access log analytics is hosted. This name should 
  point (possibly via a Caddy proxy) toward the NGINX proxy that makes the 
  WebSocket service available (via the GoAccess script).
- `proxy_range`: CIDR range of trusted IP addresses that may host the first 
  layer of proxies in front of the NGINX proxy (for example the Caddy proxies). 
  Requests from these addresses may provide headers with the real IP address of 
  the original request, which are used instead of the proxy's IP address.
- `auth_cert`: Filesystem path to a certificate used for validating the HTTPS 
  connection to the `control_host`. If a `SERVER_CERTIFICATE` environment is 
  not set, then this is also used as the path on the Docker host machine during 
  the `docker-compose` tests to provide this path within the Docker instance.
- `allow_range` (array): CIDR ranges of IP addresses that are allowed to access 
  the access log analytics.
- `primary_dns`: IP address of an external DNS server that allows Docker 
  instances during the `docker-compose` tests to look up external domain names, 
  aside from those used for the Docker instances. Proper DNS resolution may be 
  necessary to properly set up the visualizations under test.

Configuration items that have keys ending in `_url` may be processed to direct 
toward an organization-specific path, in case multiple organizations are hosted 
in the same environment. The value is searched for the substring 
`$organization`, possibly after slashes. These can be replaced with the actual 
organization that the build is for. In some cases, it is removed only to allow 
NGINX rules to add it in front of the path using `hub_regex`. The environment 
variables `$VISUALIZATION_ORGANIZATION` and `$VISUALIZATION_COMBINED` determine 
what happens with the substring, as it can also become "/combined" for the 
latter. The environment variables can also play a role elsewhere, such as in 
the proxy server configuration and test environment.

Note that configuration items that have keys ending in `_host` or `_server` may 
be set to "fake" values when only a portion of the final NGINX configuration is 
actually used, for example when some resources are not made available. The 
configuration values should still be set to valid domain names so that they can 
be used within the `docker-compose` network during the tests.

Whereas the configuration file is likely necessary to be copied and changed, 
there are other files within the repository that can be modified to adjust what 
is available on the visualization site. We will briefly introduce these files, 
as adjustments should be considered more like code changes.

The navigation bar is configured in `navbar.json` as well as 
`navbar.$VISUALIZATION_ORGANIZATION.js`. The format is defined in the 
`@gros/visualization-ui` package for the `Navbar` class, with the addition that 
strings can have `$organization` substrings replaced.

The available visualizations are configured in `visualizations.json`. The 
structure is based on the layout of the dashboard, but the items defined in it 
also determine which visualizations are actually made available in the proxy 
server configuration as well as within the tests. The JSON object is used as 
a Mustache structure within the index template, and so they may contain 
Mustache items to refer to configuration items.

Localization of the visualization site is in `lib/locales.json`. The messages 
in it are only used when referred from JavaScript code using the `Locales` 
class from the `@gros/visualization-ui` package, or when using the 
`data-message` attribute within HTML.

## Running

The visualization can be built using Node.js and `npm` by running `npm install` 
and then either `npm run watch` to start a development server that also 
refreshes browsers upon code changes, or `npm run production` to create 
a minimized bundle. The resulting HTML, CSS and JavaScript is made available in 
the `www` directory.

As mentioned in the [dependencies](#dependencies), this repository also 
contains a `Dockerfile` specification for a Docker image that can perform the 
installation of the app and dependencies, which allows building the 
visualization site within there, removing the need for a global Node.js 
installation. The `Jenkinsfile` contains appropriate steps for a Jenkins CI 
deployment, including the tests, visualization building and publishing.

During the build, JavaScript in order to construct a common navigation bar is 
separated from the main JavaScript bundle in `vendor.js`. The visualizations 
and prediction site also refer to this file to display the navigation bar.

A full production environment uses the generated proxy server configuration in 
order to deploy the reverse proxy layer(s) that allow access to all the 
visualizations and other resources. Either the `caddy` docker compose file can 
be set up, and the main `nginx.conf` plus the files generated in the `nginx` 
directory can be supplied to the NGINX service, or a subset of these files may 
be used, for example to host all under one domain, with additional local 
configuration.
