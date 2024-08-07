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
- [NGINX](https://www.nginx.com/) for proxy access and/or static file hosting 
  from a central server listening on specific ports. It can also use Host-based 
  proxying. Complete, direct hosting is possible but may require additional, 
  separate server configuration.
- [Apache](https://httpd.apache.org/) as an alternative to NGINX, for proxy 
  access and/or static file hosting from a central server listening on specific 
  ports. It can also use Host-based proxying. Complete, direct hosting is 
  possible but may require additional, separate server configuration.

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
performs the tests must have Docker Compose V2. In addition, tools such as 
Bash, Git, `jq`, `awk`, `sed`, `grep` and `xargs` must be available and 
GNU-like (POSIX-compliant may not be enough). A SonarQube Scanner must be 
registered in Jenkins. The server agent that performs the publishing must have 
Docker Compose V2, Node.js, `curl` and `rsync` as well. Details for configuring 
Jenkins servers and agents are outside the scope of this documentation, 
although some details may be available in other GROS documentation. The 
integration tests may be able to be run outside a Jenkins job, but support for 
this is limited and it requires passing additional environment variables.

The deployment assumes an NGINX or Apache service and potentially a Docker 
Compose installation some which can be set up using (some of) the configuration 
files that we build from the templates in this repository.

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
main configuration point is usually the `config.json` file, which can be copied 
from `lib/config.json` to the root of the repository in order to make local 
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
- `base_url`: The absolute URL to the base website where other static resources 
  are located. This is used to link to the base website in the navigation bar 
  and to make certain URLs absolute like schema identifiers and canonical URLs. 
  If it is left empty, then some of those URLs will not have a protocol and 
  domain name or use the current location as base.
- `blog_url`: The URL to the blog. This may include a protocol and domain name, 
  but does not need to in case all the resources are hosted on the same domain. 
  The remainder is a path to the root of the blog. If this is empty, then no 
  blog is available.
- `discussion_url`: The URL to the discussion forum. This may include 
  a protocol and domain name, but does not need to in case all the resources 
  are hosted on the same domain. The remainder is a path to the root of the 
  forum. If this is empty, then no forum is available.
- `download_url`: The URL to default download links on the dashboard. This can 
  be overwritten by specific download URLs by the visualizations and an altered 
  value may work with the redirections provided by the NGINX or Apache proxy, 
  so care should be taken when adjusting this. This may be helpful when direct 
  access to downloads are available. If this is empty, then no download links 
  are shown on the dashboard.
- `jira_url`: URL that is used in some navigation bars to link to a Jira 
  instance.
- `blog_host`: Domain name of an internal server where the blog is hosted.
- `blog_server`: Domain name of an external server that provides access to the 
  blog. This name should point (possibly via a Caddy proxy) toward the NGINX or 
  Apache proxy that makes the server available.
- `discussion_host`: Domain name of an internal server where the discussion 
  forum is hosted.
- `discussion_server`: Domain name of an external server that provides access 
  to the discussion forum. This name should point (possibly via a Caddy proxy) 
  toward the NGINX or Apache proxy that makes the server available.
- `visualization_server`: Domain name of an external server that provides 
  access to the visualization dashboard and every visualization (except 
  predictions). This name should point (possibly via a Caddy proxy) toward the 
  NGINX or Apache proxy that makes the server available.
- `www_server`: Domain name of an external server that listens on a "www" 
  address. This server redirects to the visualization server. This name should 
  point (possibly via a Caddy proxy) toward the NGINX or Apache proxy that 
  makes the redirection service available.
- `prediction_server`: Domain name of an external server that provides access 
  to the predictions. This name should point (possibly via a Caddy proxy) 
  toward the NGINX or Apache proxy that makes the server available.
- `hub_organizations` (array): When multiple organizations are hosted in the 
  same environment, an array of objects containing organizations, navigation 
  data and branch names can be added to make them available cross-builds. For 
  tests, they provide a build and serve dummy data for visualizations on 
  multiple branches. The test routes only consider the `visualization-site` and 
  `prediction-site` as keys in each object, and their values should provide 
  a branch name that the `visualization_branch` and `prediction_branch` may 
  respectively point to for NGINX testing, or the branch names generated using 
  `hub_mapping` for Apache testing. The organizations objects in this array 
  also define how items in a navigation bar dropdown should appear, with 
  titles, content/alternative text locales, images (plus width/height/style 
  attributes) and external URLs. Finally, a key `visualizations` may have an 
  array value with the visualizations that the organization's hub hosts.
- `hub_regex`: When multiple organizations are hosted in the same environment, 
  a regular expression can be used to match the organization name which must 
  occur at the start of the path, and place the matched parts into variables 
  for later use in rewrite rules of NGINX or Apache. Use `(?<groupname>...)` 
  for capturing matches for compatibility across proxy servers. To avoid 
  renumbering issues, this regular expression should not contain unnamed match 
  captures `(...)`.
- `hub_mapping` (object): Groups of environment variable names to replace the 
  matched substrings from the regular expression from `hub_regex` in. Only used 
  for Apache, when hosting multiple organizations in the same environment. 
  Group keys can be "hub", "visualization" and "prediction", corresponding to 
  the visualization-site itself, the visualizations and the prediction-site, 
  respectively. Each variable within the group has an object with "input", 
  "default", and "output" keys, which are used to build a `RewriteMap`. The 
  input and default can refer to other variables with dollar signs. The output 
  mapping cannot contain spaces or empty strings in both the keys and values. 
  In addition to the `hub_regex` variables, the "prediction" group may also 
  transform a `branch_organization` variable to map paths to organizations in 
  (combined) prediction setups. The mapping is also used for determining the 
  available prediction path setups on the server for the OpenAPI specification, 
  and for copying the published visualizations on master branches to the proper 
  default organizations. In NGINX, one can instead alter variables captured 
  from regular expressions using `hub_branch`, `visualization_branch` and 
  `prediction_branch`.
- `branch_maps_path`: Filesystem path where the rewrite maps for the Apache 
  configuration are expected to reside. The map files are written to 
  `httpd/maps` in this repository, but may be mapped to another absolute path. 
  This affects the path within the Docker instance during the `docker-compose` 
  paths, but can also be helpful when using (portions of) the configuration on 
  an Apache server.
- `hub_redirect`: When multiple organizations are hosted in the same 
  environment, variables from a matched organization at the start of the path 
  using `hub_regex` can be used in a rewrite that redirects to another URL. It 
  is assumed that this configuration value produces an absolute URL. For NGINX, 
  use dollar-sign variables; for Apache, use environment variables named with 
  `hub_mapping` with `%{...}` syntax.
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
- `files_share_id`: Identifier of a published share on an ownCloud instance 
  with files that are made available in addition to the prediction resources. 
  If this is an empty string, then the paths to the files list and specific 
  files are not passed through to ownCloud from the NGINX or Apache proxy.
- `control_host`: Domain name of an internal server where secure resources are 
  hosted, including encryption services and access control checks. This domain 
  must be accessible through HTTPS from the NGINX or Apache proxy. This can be 
  set to an empty string to disable proxy connections to endpoints for 
  encrypting names of developers and checking project group access, as used in 
  some visualizations. An empty string also makes the Caddy proxy configuration 
  unusable, so only leave this empty if a portion of the configuration is used.
- `websocket_server`: Domain name of an external server where a WebSocket for 
  real-time updates of access log analytics is hosted. This name should point 
  (possibly via a Caddy proxy) toward the NGINX or Apache proxy that makes the 
  WebSocket service available (via the GoAccess script).
- `proxy_nginx` (boolean): Whether to use NGINX to provide access to the other 
  servers or host the direct files. If set to false, use Apache HTTP Server 
  instead. Affects the test as well as which configuration is generated.
- `proxy_range`: CIDR range of trusted IP addresses that may host the first 
  layer of proxies in front of the NGINX or Apache proxy, for example the Caddy 
  proxies. Requests from these addresses may provide headers with the real IP 
  address of the original request, which are used instead of the proxy's IP 
  address.
- `proxy_port_in_redirect` (boolean): Whether to make the NGINX or Apache proxy 
  specify the port number when a redirect is generated. If a Caddy proxy is in 
  front of it, then this is most likely not wanted. Similarly, if only portions 
  of the configuration files are used, then this is also not useful to enable.
- `auth_cert`: Filesystem path to a certificate used for validating the HTTPS 
  connection to the `control_host`. If a `$SERVER_CERTIFICATE` environment is 
  not set, then this is also used as the path on the Docker host machine during 
  the `docker-compose` tests to provide this path within the Docker instance.
- `allow_range` (array): CIDR ranges of IP addresses that are allowed to access 
  the access log analytics.
- `goaccess_path`: Filesystem path to the location where the GoAccess interface 
  is hosted. The directory should contain an `analytics` subpath which holds 
  the actual web interface. This can be set to an empty string to disable the 
  GoAccess endpoint.
- `goaccess_log_path`: Filesystem path to log file location. Access logs stored 
  in this path (including rotated and possibly GZip-encoded logs) are followed.
- `swagger_openapi_url`: URL prefix to use for the OpenAPI specification files 
  that are made available in the Swagger UI. The default value of `./` works 
  well for the Docker instance, but if the OpenAPI files are meant to be stored 
  elsewhere then another path is possible. For production builds of a static 
  file hosting setup with `jenkins_direct`, this value is set to the absolute 
  path of the direct hosting root, and additional OpenAPI files rather than 
  just the prediction API are made available.
- `swagger_validator_url`: URL to use to connect to the validator. The default 
  value of `/validator` works well for the Docker compose network. If it is set 
  to an empty string, then the online validator is used. Can be set to `none` 
  to disable the validator. For production builds of a static file hosting 
  setup with `jenkins_direct`, we use the online validator.

Configuration items that have keys ending in `_url` may be processed to direct 
toward an organization-specific path, in case multiple organizations are hosted 
in the same environment. The value is searched for the substring 
`$organization`, possibly after slashes. These can be replaced with the actual 
organization that the build is for. In some cases, it is removed only to allow 
NGINX or Apache rules to add a supported variant of it in front of the path 
using `hub_regex`, and in other cases, it may be preserved to be adjusted at 
a later moment within the visualization or hub. Specific [environment 
variables](#environment-variables) determine how the substring `$organization` 
is replaced.

Note that configuration items that have keys ending in `_host` or `_server` may 
be set to "fake" values when only a portion of the final NGINX or Apache 
configuration is actually used, for example when some resources are not made 
available. The configuration values should still be set to valid domain names 
so that they can be used within the `docker-compose` network during the tests.

### Environment variables

Several environment variables may be used when calling `npm run` or the Shell 
scripts, and may affect various contexts, such as resource paths in the HTML 
pages, the JavaScript-based navigation bar, the proxy server configuration and 
the test environment. Boolean environment variables must be set to `true` in 
order to take effect.

- `$VISUALIZATION_ORGANIZATION`: Determines the organization to use within the 
  URLs defined in the configuration.
- `$VISUALIZATION_COMBINED` (boolean): Determines whether to replace the 
  organization within the URL with `/combined`.
- `$NAVBAR_SCOPE`: Determines the navigation bar override file to use. If the 
  file `navbar.$NAVBAR_SCOPE.js` exists, then it is loaded in place of the 
  generated `navbar.json` file. See [files](#files) for more details.
- `$VISUALIZATION_ANONYMIZED` (boolean): Determines whether to show 
  a notification on the HTML page indicating that the visualizations contain 
  anonymized data and that some functionality is limited or missing.
- `$VISUALIZATION_SITE_CONFIGURATION`: Path to the main configuration file, 
  defaulting to `config.json`. If this file does not exist, then 
  `lib/config.json` is used.
- `$PREDICTION_CONFIGURATION`: Path to the configuration file of the 
  `prediction-site` visualization, which is then used during tests. By default, 
  the prediction's default configuration is used, which may be incompatible in 
  some complex combined/organization setups. Other visualizations are tested 
  with default configuration.
- `$VISUALIZATION_NAMES`: Optional space-separated list of repository names of 
  visualizations (excluding `visualization-site` itself) that should be 
  included in the navigation bar, proxy configuration, test environment setup, 
  and publishing phase. By default, all visualizations listed in the file 
  `visualizations.json` are considered.
- `$VISUALIZATION_MAX_SECONDS` (integer): Number of seconds to wait before are 
  visualizations are compiled and made available during the test setup. By 
  default, 60 seconds is allocated, which may be too short for some nodes.
- `$REPO_ROOT`: Directory to store the Git repositories of the visualizations 
  during the test setup. Relative to the current directory. By default, `repos` 
  is created as a subdirectory. If another directory is used, then existing 
  clones are left as-is with no up-to-dateness checks and dependencies are 
  backed up so that they do not interfere with the test setup.
- `$SERVER_CERTIFICATE`: Path to the HTTPS certificate to use in the test setup 
  when requesting upstream resources for encryption and access checks. By 
  default, this is the `auth_cert` from the configuration, but this can be set 
  to use a different path at the host device than in the Docker test setup.
- `$PUBLISH_PRODUCTION`: A boolean variable which indicates whether to perform 
  a copy for potential publication from the current feature branch instead of 
  only doing so when on a main branch. Note that main branches are skipped in 
  this case, so the publication may not have organization-specific paths.
- `$JENKINS_HOME`: Provided by 
  [Jenkins](https://www.jenkins.io/doc/book/managing/system-properties/#jenkins_home) 
  and used by the `copy.sh` script as the root from which to collect artifacts 
  and visualization HTML reports for publishing.
- `$BRANCH_NAME`: Provided by [Jenkins Multibranch 
  Pipeline](https://www.jenkins.io/doc/book/pipeline/multibranch/#additional-environment-variables) 
  and used by the test environment in order to separate Docker resources when 
  building dependencies for visualizations under test.
- `$BUILD_NUMBER`, `$BUILD_TAG`, `$BUILD_URL`, `$NODE_NAME`: Provided by 
  [Jenkins](https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#using-environment-variables) 
  and used by the test environment in order to track build context for 
  reporting and naming purposes.

### Files

Whereas the configuration file, usually located at `config.json`, is likely 
necessary to be copied (from `lib/config.json`) and changed, there are other 
files within the repository that can be modified to adjust what is available on 
the visualization site. We will briefly introduce these files, as adjustments 
should be considered more like code changes.

The navigation bar is configured in `navbar.json.mustache`, with optional 
contextual overrides in `navbar.$NAVBAR_SCOPE.js`. The format is defined in the 
`@gros/visualization-ui` package for the `Navbar` class, with the addition that 
URLs can have `$organization` substrings replaced, and various Mustache 
operations can take place to fill the navigation bar with menus/links defined 
elsewhere, such as visualizations and organizations. `navbar.$NAVBAR_SCOPE.js` 
should, if used, refer to `navbar.json` and use simple JavaScript operations to 
augment it, though the use of this file may not be necessary when specifics for 
an organization can be set by changing other files, such as `config.json` and 
`visualizations.json`.

The available visualizations are configured in `visualizations.json`. The 
structure is based on the layout of the dashboard, but the items defined in it 
also determine which visualizations are actually made available in the 
navigation bar, proxy server configuration as well as within the tests. The 
JSON object is used as a Mustache structure within the index template and the 
navigation bar, and so they may contain Mustache items to refer to certain
configuration items, such as URLs.

Localization of the visualization site is in `lib/locales.json`. The messages 
in it are used when referred from JavaScript code using the `Locales` class 
from the `@gros/visualization-ui` package, or when using the `data-message` 
attribute within the HTML templates.

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

A non-static production environment can make use of the generated proxy server 
configuration in order to deploy the reverse proxy layer(s) that allow access 
to all the visualizations and other resources. Optionally, the `caddy` docker 
compose file can be set up. Next, either the main `nginx.conf` plus the files 
generated in the `nginx` directory can be supplied to the NGINX service, or 
likewise with `httpd.confg` and the generated files in the `httpd` directory 
for the Apache service. Alternatively, a subset of these files may be used, for 
example to host all under one domain, with additional local configuration.

Documentation based on JSON schema specification files from various GROS 
repositories can be built with the `doc` directory. This requires installing 
the some Python dependencies, preferably first setting up a `virtualenv`, then 
running `pip install -r doc/requirements.txt`. The file `doc/source/conf.py` 
contains configuration for the documentation, including paths or URLs to the 
schema files, which can be altered to use local paths. When run on the Jenkins 
server to create static documentation, these paths may be defined through the 
`doc.sh` script which locates the JSON schemas as part of archives and modules 
available in the current workspace and beyond.

A static production environment can make use of the result of the Bash script 
`copy.sh` when run on the Jenkins server in order to create a document root 
directory with the organizational hubs, all the visualizations, JSON schemas, 
OpenAPI specifications and Swagger UI available for publishing on a static file 
hosting server. This server may make use of the NGINX or Apache configurations, 
which in their compiled form properly route the prediction site and error 
pages, among others. Like other parts, the `copy.sh` script requires specific 
[configuration](#configuration) for mapping hub paths, selecting organizations, 
producing paths and URLs and accessing Jenkins for the publishable 
visualizations, archived files and prediction branches.
