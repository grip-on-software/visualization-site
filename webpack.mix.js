/**
 * Entry point for laravel-mix/webpack compilation and template expansion.
 *
 * Copyright 2017-2020 ICTU
 * Copyright 2017-2022 Leiden University
 * Copyright 2017-2023 Leon Helwerda
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
const fs = require('fs'),
      path = require('path'),
      { URL } = require('url'),
      mix = require('laravel-mix'),
      _ = require('lodash'),
      mustache = require('mustache'),
      HtmlWebpackPlugin = require('html-webpack-plugin');

const spec = JSON.parse(fs.readFileSync('lib/locales.json'));
const message = (key) => `<span data-message="${key}">${spec.en.messages[key]}</span>`;
const messages = _.transform(spec.en.messages, (result, value, key) => {
    result[`message-${key}`] = message(key);
}, {});
const locale = (key) => _.mapValues(spec, language => language.messages[key]);

let configFile =
    typeof process.env.VISUALIZATION_SITE_CONFIGURATION !== "undefined" ?
    process.env.VISUALIZATION_SITE_CONFIGURATION : 'config.json',
    config = path.resolve(__dirname, configFile);
if (!fs.existsSync(config)) {
    configFile = 'lib/config.json';
    config = path.resolve(__dirname, configFile);
}
const configuration = JSON.parse(fs.readFileSync(config));
if (process.env.NODE_ENV === 'test') {
    // In test:
    // - Change visualization URL to an absolute URL to the visualization server
    //   (caddy proxy domain name) so prediction site can obtain resources, but
    //   only if the URL is not already absolute (assume correct config)
    // - Always use jenkins reverse proxy
    // - Enable owncloud reverse proxy rules for prediction files
    // - Make redirects hide port in redirect for upstream caddy proxy
    // - Enable control host reverse proxy for access/encrypt endpoints
    configuration.base_url = `http://${configuration.visualization_server}`;
    configuration.visualization_url = new URL(configuration.visualization_url,
        configuration.base_url
    ).href;
    configuration.jenkins_direct = '';
    configuration.files_share_id = 'test';
    configuration.proxy_port_in_redirect = false;
    if (configuration.control_host === '') {
        configuration.control_host = 'control.gros.test';
    }
}
else if (process.env.NODE_ENV === 'production' && configuration.jenkins_direct) {
    // In production with a direct host setup, build Swagger configuration
    // without a subdirectory for OpenAPI files, and use online validator for
    // the extracted copy.
    configuration.swagger_openapi_url = '/';
    configuration.swagger_validator_url = '';
}

// Replace organization parameter with environment variable if necessary.
// Used for visualization links and HTML configuration
const urlConfiguration = _.mapValues(configuration,
    (value, key) => {
        if (!key.endsWith('_url')) {
            return value;
        }
        if (process.env.VISUALIZATION_COMBINED === "true") {
            return value.replace("/$organization", "/combined");
        }
        return value.replace(/(\/)?\$organization/,
            typeof process.env.VISUALIZATION_ORGANIZATION !== 'undefined' ?
            "$1" + process.env.VISUALIZATION_ORGANIZATION : ''
        );
    }
);

// Read list of available visualizations in groups for main page display,
// and add variables for expansion
let visualizations = JSON.parse(fs.readFileSync('visualizations.json'));
if (typeof process.env.VISUALIZATION_NAMES !== "undefined") {
    const names = new Set(process.env.VISUALIZATION_NAMES.split(' '));
    visualizations.groups = _.map(visualizations.groups,
        (group) => _.assign({}, group, {
            items: _.filter(group.items, (item) => names.has(item.id))
        })
    );
}
visualizations.groups = _.map(visualizations.groups,
    (group) => _.assign({}, group, {
        title: message(`${group.id}-title`),
        items: _.map(group.items, (item) => _.assign({}, {
            index: true,
            nginx: true,
            repo: item.id
        }, item, {
            show: typeof item.url !== "undefined" ?
                mustache.render(item.url, urlConfiguration) : item.id,
            download: typeof item.download !== "undefined" ?
                mustache.render(item.download, urlConfiguration) :
                `${urlConfiguration.download_url}${item.id}.zip`,
            icon_parts: item.icon,
            icon: `<span class="icon">
                <i class="${_.map(item.icon, (part, i) => i === 0 ? part : `fa-${part}`).join(' ')}" aria-hidden="true"></i>
            </span>`,
            title: message(`${item.id}-title`),
            content: message(`${item.id}-content`)
        }))
    })
);
const visualization_names = _.flattenDeep(_.map(visualizations.groups,
    (group) => _.map(group.items, (item) => item.index ? item.repo : [])
));
const visualization_nginx = _.flattenDeep(_.map(visualizations.groups,
    (group) => _.map(group.items, (item) => item.nginx ? item.id : [])
));
fs.writeFileSync(path.resolve(__dirname, 'visualization_names.txt'),
    visualization_names.join(' ')
);

// NGINX/Apache and Docker-compose service template configuration
const proxy_logs = {
    nginx: {
        error: {
            'test': 'notice',
            'development': 'warn',
            'production': 'error'
        },
        rewrite: {
            'test': 'on',
            'development': 'off',
            'production': 'off'
        }
    },
    httpd: {
        error: {
            'test': 'trace4',
            'development': 'debug',
            'production': 'error'
        },
        rewrite: {
            'test': 'trace6',
            'development': 'trace3',
            'production': 'warn'
        }
    }
};
const httpdRewrite = (pattern, path, flags) => [
    `RewriteCond %{REQUEST_URI} ${pattern}`,
    `RewriteRule ^ ${path.replace(/\$(\d+)/g, '%$1')} [${flags.join(',')}]`
].join('\n    ');
const httpdMatch = (_, match) => `%{ENV:MATCH_${match.toUpperCase()}}`;
const convertMatches = function(job, branch, file) {
    if (configuration.proxy_nginx) {
        return [job, branch, file];
    }
    const group = job == "visualization-site" ? "hub" :
        (job.startsWith("prediction") ? "prediction" : "visualization");
    return _.map([job, branch, file], (env) => replaceMatches(group, env));
};
const replaceMatches = (group, path) => configuration.proxy_nginx ? path :
    path.replace(/\$([_a-zA-Z]+)/g, (substring, match) => {
        const mapping = configuration.hub_mapping[group][match];
        if (mapping) {
            const mapInput = mapping.input.replace(/\$([_a-zA-Z]+)/g,
                httpdMatch
            );
            const mapDefault = mapping["default"] ?
                mapping["default"].replace(/\$([_a-zA-Z]+)/g, httpdMatch) :
                "";
            return `\${${group}_${match}:${mapInput}|${mapDefault}}`;
        }
        return httpdMatch(substring, match);
    });
const nginxRewrite = (pattern, path, redirect=false) => redirect ?
    `rewrite ${pattern} ${path} permanent;` : (path instanceof URL ? [
        `rewrite ${pattern} ${path.pathname} break;`,
        `proxy_pass ${path.origin};`
    ].join('\n    ') : `rewrite ${pattern} ${path} break;`);

if (!configuration.proxy_nginx) {
    _.forEach(["hub", "visualization", "prediction"], (group) => {
        _.forEach(configuration.hub_mapping[group], (mapping, env) => {
            const mapFile = `${group}_${env}.txt`;
            fs.writeFileSync(path.resolve(__dirname, `httpd/maps/${mapFile}`),
                _.map(mapping.output,
                    (value, key) => `${key} ${value}`
                ).join('\n')
            );
        });
    });
}

const proxy = configuration.proxy_nginx ? 'nginx' : 'httpd';
const control_host_index = configuration.control_host.indexOf('.');
const domain_index = configuration.visualization_server.indexOf('.');
const internal_domain_index = configuration.jenkins_host.indexOf('.');
const srvConfiguration = _.assign({}, visualizations, _.mapValues(configuration,
    // Remove any organization parameters from URLs
    // The injected branch setter (hub_regex with associated configuration) is
    // not adjusted and is responsible for routing the correct organization(s),
    // or in the case of redirects and error pages, the hub_redirect variable
    (value, key) => key.endsWith('_url') ?
        value.replace(/\/?\$organization/, '') : value
), {
    config_file: configFile,
    control_hostname: configuration.control_host.slice(0, control_host_index),
    control_domain: configuration.control_host.slice(control_host_index + 1),
    domain: configuration.visualization_server.slice(domain_index + 1),
    internal_domain: configuration.jenkins_host.slice(internal_domain_index + 1),
    repo_root: typeof process.env.REPO_ROOT !== "undefined" ?
        process.env.REPO_ROOT : 'repos',
    server_certificate: typeof process.env.SERVER_CERTIFICATE !== "undefined" ?
        process.env.SERVER_CERTIFICATE : configuration.auth_cert,
    branch_name: typeof process.env.BRANCH_NAME !== "undefined" ?
        process.env.BRANCH_NAME : '',
    user_id: process.getuid(),
    group_id: process.getgid(),
    visualization_names: visualization_nginx,
    prediction_organizations: _.includes(visualization_names, 'prediction-site') ?
        configuration.hub_organizations : [],
    visualization_organizations: _.map(configuration.hub_organizations, 'visualization-site'),
    join: function() {
        return function(text, render) {
            // Remove last character
            return render(text).slice(0, -1);
        };
    },
    path: function() {
        return function(text, render) {
            const path = render(text);
            if (path.charAt(0) === '/' && path.charAt(1) !== '/') {
                return path;
            }
            try {
                return (new URL(path)).pathname;
            }
            catch (e) {
                return '/';
            }
        };
    },
    url: function() {
        // Generate an absolute path URL
        return function(text, render) {
            const url_parts = render(text).split('/');
            const server = `http://${url_parts.shift()}`;
            return (new URL(url_parts.join('/').replace(server, ''), server))
                .pathname.replace('//', '/').replace(/^\/\$/, '$')
                .replace(/(?:^\/)?%%7B(ENV:MATCH_[_a-zA-Z]+)%7D/g, '%{$1}');
        };
    },
    upstream: function() {
        return function(text, render) {
            if (configuration.proxy_nginx) {
                return `$${render(text)}`;
            }
            const host_parts = render(text).split(':');
            const server = host_parts.shift();
            const host = configuration[`${server}_host`];
            const port = host_parts.join(':');
            return `${host}${port ? ':' : ''}${port}`;
        };
    },
    port: function() {
        return function(text, render) {
            const port = render(text);
            if (port === "") {
                return configuration.proxy_port_in_redirect ? 'on' : 'off';
            }
            return configuration.proxy_port_in_redirect ? `:${port}` : '';
        };
    },
    proxy_rewrite: function() {
        return function(text, render) {
            const [pattern, url, tags=null] = render(text).split(' ', 3);
            if (configuration.proxy_nginx) {
                return nginxRewrite(pattern, new URL(url));
            }
            let flags = tags ? tags.slice(1, -1).split(',') : [];
            flags.push('P');
            return httpdRewrite(pattern, url, flags);
        };
    },
    jenkins_rewrite: function() {
        return function(text, render) {
            const [pattern, path, tags=null] = render(text).split(' ', 3);
            let flags = tags ? tags.slice(1, -1).split(',') : [];
            if (configuration.jenkins_direct) {
                if (path.startsWith('prediction/') ||
                    path.startsWith('prediction-site/') || tags) {
                    flags.push('END');
                    // Adjust to how copy.sh places the files
                    const sitePath = path
                        .replace(/^(prediction|visualization)-site\/[^/]+/,
                            (_, group) => replaceMatches(
                                group === "visualization" ? "hub" : group,
                                `$hub/${group}`
                            )
                        )
                        .replace(/^prediction\/(.*)/, '/prediction/$1');
                    return configuration.proxy_nginx ?
                        nginxRewrite(pattern, sitePath) :
                        httpdRewrite(pattern, sitePath, flags);
                }
                return '';
            }
            if (configuration.proxy_nginx) {
                // Proxy pass handled by separate rule in configuration file
                return nginxRewrite(pattern, path);
            }
            flags.push('P');
            const url = `http://${configuration.jenkins_host}:8080${path}`;
            return httpdRewrite(pattern, url, flags);
        };
    },
    jenkins_redirect: function() {
        return function(text, render) {
            const [pattern, path] = render(text).split(' ');
            return configuration.proxy_nginx ?
                nginxRewrite(pattern, path, true) :
                httpdRewrite(pattern, path, ['L', 'R=301']);
        };
    },
    hub_rewrite: configuration.hub_regex.replace(/(?<!\\])\(\?<\w+>/g, "(?:"),
    hub_redirect: configuration.proxy_nginx ? configuration.hub_redirect :
        configuration.hub_redirect.replace(/\$([_a-zA-Z]+)/g, httpdMatch),
    hub_branch: configuration.proxy_nginx ? configuration.hub_branch :
        "RewriteBase /",
    visualization_branch: configuration.proxy_nginx ?
        configuration.visualization_branch : "RewriteBase /",
    prediction_branch: configuration.proxy_nginx ?
        configuration.prediction_branch : "RewriteBase /",
    branch_maps: function() {
        return function(text, render) {
            const group = render(text);
            if (configuration.proxy_nginx) {
                return configuration[`${group}_branch`];
            }
            return _.map(configuration.hub_mapping[group], (mapping, env) => {
                const map = `${group}_${env}`;
                const mapPath = `${configuration.branch_maps_path}/${map}.txt`;
                return `RewriteMap ${map} txt:${mapPath}`;
            }).join('\n');
        };
    },
    jenkins_report: function() {
        return function(text, render) {
            const url_parts = render(text).split('/');
            const [job, branch, file] = convertMatches(
                url_parts.shift(), url_parts.shift(), url_parts.join('/')
            );
            if (configuration.jenkins_direct) {
                // Path prefix added (for nginx) in jenkins_rewrite
                return `${job}/${branch}/${file}`;
            }
            return `${configuration.jenkins_path}/job/build-${job}/job/${branch}/Visualization/${file}`;
        };
    },
    jenkins_artifact: function() {
        return function(text, render) {
            const url_parts = render(text).split('/');
            const [job, branch, file] = convertMatches(
                url_parts.shift(), url_parts.shift(), url_parts.join('/')
            );
            if (configuration.jenkins_direct) {
                // Path prefix added (for nginx) in jenkins_rewrite
                return `${job}/${branch}/${file}`;
            }
            return `${configuration.jenkins_path}/job/create-${job}/job/${branch}/lastStableBuild/artifact/${file}`;
        };
    },
    jenkins_branches: configuration.jenkins_direct ? '/branches.json':
        `${configuration.jenkins_path}/job/create-prediction/api/json?tree=jobs[name,lastStableBuild[description,duration,timestamp]]`,
    error_log: _.get(proxy_logs, [proxy, 'error', process.env.NODE_ENV],
        'error'
    ),
    rewrite_log: _.get(proxy_logs, [proxy, 'rewrite', process.env.NODE_ENV],
        'off'
    )
});

const templates = [
    `${proxy}.conf`, `${proxy}/blog.conf`, `${proxy}/discussion.conf`,
    `${proxy}/prediction.conf`, `${proxy}/visualization.conf`,
    `${proxy}/websocket.conf`,
    'caddy/docker-compose.yml', 'caddy/ws', 'caddy/www',
    'test/docker-compose.yml', 'swagger/docker-compose.yml'
];
templates.forEach((template) => {
    try {
        fs.writeFileSync(template,
            mustache.render(fs.readFileSync(`${template}.mustache`, 'utf8'),
                srvConfiguration
            )
        );
    }
    catch (e) {
        throw new Error(`Could not render ${template}.mustache`, {cause: e});
    }
});

// Generate configuration to import into the navbar builder
const jsConfiguration = _.assign({}, _.pickBy(configuration,
    (value, key) => !key.startsWith('jenkins_direct') && key.endsWith('_url')
), {
    organization:
        typeof process.env.VISUALIZATION_ORGANIZATION !== 'undefined' ?
        process.env.VISUALIZATION_ORGANIZATION : '',
    visualizations: _.assign({}, _.mapValues(
        _.keyBy(configuration.hub_organizations, 'organization'),
        'visualizations'
    ), {combined: ["prediction"]})
});
const configAlias = path.resolve(__dirname, 'config-alias.json');
fs.writeFileSync(configAlias, JSON.stringify(jsConfiguration));

const combinedUrl = configuration.prediction_url.replace("/$organization",
    "/combined"
);
// URLs in navbar should be rendered as, e.g., {"config": "visualization_url"}
// so that the expansion can take place later, which is relevant for combined
// visualizations for example, where we may want it to lead to a visualization
// for the main organization instead, or for switching organizations.
const delayedUrlConfiguration = _.assign({}, _.mapValues(jsConfiguration,
    (url, key) => key.endsWith('_url') ? JSON.stringify({config: key}) : url
), {
    config: function() {
        return function(text, render) {
            return _.map(_.filter(text.split(/({{{?[^}]+}}}?)/), bit => bit),
                bit => bit.startsWith('{') ? render(bit) : JSON.stringify(bit)
            ).join(', ');
        };
    }
});
const navbarConfiguration = _.assign({}, delayedUrlConfiguration, {
    alt: function() {
        return this.locale ? JSON.stringify(this.locale) :
            this.organization;
    },
    content: function() {
        return this.title ? JSON.stringify(this.title) : this.organization;
    },
    organizations: _.map(configuration.hub_organizations,
        (org, index) => _.assign({}, org, {
            active: process.env.VISUALIZATION_COMBINED !== "true" &&
                (org.organization === process.env.VISUALIZATION_ORGANIZATION ||
                    index === 0 &&
                    typeof process.env.VISUALIZATION_ORGANIZATION === "undefined"
                ),
            hub_url: configuration.visualization_url.replace(
                "/$organization", `/${org.organization}`
            )
        })
    ),
    base_url: configuration.base_url,
    combined: process.env.VISUALIZATION_COMBINED === "true",
    combined_url: combinedUrl,
    visualizations: _.map(visualizations.groups, (group, index) => {
        const items = _.reduce(group.items, (result, item) => {
            if (!item.index) {
                return result;
            }
            const url = item.url || `{{{visualization_url}}}${item.id}`;
            const visualizationUrl = mustache.render(
                `{{#config}}${url}{{/config}}`, delayedUrlConfiguration
            );
            const languageParameter = item.language_parameter ?
                `?${item.language_parameter}=` : '?';
            const titles = locale(`${item.id}-title`);
            result.push(`
                            {
                                "type": "link",
                                "id": "visualization-${item.id}",
                                "url": [
                                    ${visualizationUrl},
                                    ${JSON.stringify(languageParameter)},
                                    {"locale": "lang"}
                                ],
                                "icon": ${JSON.stringify(item.icon_parts)},
                                "content": ${JSON.stringify(titles)}
                            }`
            );
            return result;
        }, []);
        if (!_.isEmpty(items) &&
            index !== visualizations.groups.length - 1) {
            items.push(`
                            {
                                "type": "divider"
                            }`
            );
        }
        return items.join(',');
    }).join(',')
});
try {
    fs.writeFileSync("navbar.json",
        mustache.render(fs.readFileSync(`navbar.json.mustache`, 'utf8'),
            navbarConfiguration
        )
    );
}
catch (e) {
    throw new Error('Could not render navbar.json.mustache', {cause: e});
}
let navbar = path.resolve(__dirname, `navbar.${process.env.NAVBAR_SCOPE}.js`);
if (!fs.existsSync(navbar)) {
    navbar = path.resolve(__dirname, 'navbar.json');
}

// Generate prediction API specification configuration
const predictionPaths = _.flatten(_.map(_.concat(_.keys(_.get(configuration,
    ['hub_mapping', 'prediction', 'hub', 'output'], {}
)), ""), (hub) => _.map(_.keys(_.get(configuration,
    ['hub_mapping', 'prediction', 'branch_organization', 'output'], {}
)), (org) => `"${hub}${org}"`)));
const apiConfiguration = _.assign({}, _.mapValues(configuration,
    (value, key) => key.endsWith('_url') ?
        value.replace(/\/?\$organization/, '{organization}') : value
), {
    prediction_paths: _.isEmpty(predictionPaths) ? '""' :
        _.join(predictionPaths, ', '),
    prediction_path: _.isEmpty(predictionPaths) ? '""' : predictionPaths[0],
    example_file: function() {
        return function(text, render) {
            const data = text.split(':');
            const name = data.shift();
            const example = JSON.parse(data.join(':'));
            const value = fs.readFileSync(example.externalValue, 'utf8');
            example.value = example.externalValue.endsWith('json') ?
                JSON.parse(value) : value;
            delete example.externalValue;
            return `${name}: ${JSON.stringify(example)}`;
        };
    }
});
try {
    fs.writeFileSync("openapi.json",
        mustache.render(fs.readFileSync(`openapi.json.mustache`, 'utf8'),
            apiConfiguration
        )
    );
}
catch (e) {
    throw new Error('Could not render openapi.json.mustache', {cause: e});
}

// Generage configuration for HTML pages
const htmlConfiguration = _.assign({}, urlConfiguration, messages,
    visualizations, {
        anonymized: process.env.VISUALIZATION_ANONYMIZED === "true"
    }
);

Mix.paths.setRootPath(__dirname);
mix.setPublicPath('www/')
    .setResourceRoot(typeof process.env.BRANCH_NAME !== 'undefined' &&
        process.env.BRANCH_NAME.endsWith('master') ?
        htmlConfiguration.visualization_url : '/'
    )
    .js('lib/index.js', 'www/bundle.js')
    .js('./lib/build.js', 'www/vendor.js')
    .sass('res/main.scss', 'www/main.css')
    .sass('res/navbar.scss', 'www/navbar.css')
    .browserSync({
        proxy: false,
        server: 'www',
        files: [
            'www/**/*.js',
            'www/**/*.css'
        ]
    })
    .webpackConfig({
        output: {
            path: path.resolve('www/'),
            publicPath: typeof process.env.BRANCH_NAME !== 'undefined' &&
                process.env.BRANCH_NAME.endsWith('master') ?
                htmlConfiguration.visualization_url : '.'
        },
        module: {
            rules: [ {
                test: /\.mustache$/,
                loader: 'mustache-loader',
                options: {
                    tiny: true,
                    render: htmlConfiguration
                }
            } ]
        },
        plugins: [
            new HtmlWebpackPlugin({
                template: 'template/index.mustache',
                inject: 'body'
            }),
            new HtmlWebpackPlugin({
                template: 'template/401.mustache',
                filename: '401.html',
                inject: 'body'
            }),
            new HtmlWebpackPlugin({
                template: 'template/403.mustache',
                filename: '403.html',
                inject: 'body'
            }),
            new HtmlWebpackPlugin({
                template: 'template/404.mustache',
                filename: '404.html',
                inject: 'body'
            }),
            new HtmlWebpackPlugin({
                template: 'template/50x.mustache',
                filename: '50x.html',
                inject: 'body'
            })
        ],
        resolve: {
            alias: {
                'navbar.spec$': navbar,
                'config.json$': configAlias
            }
        }
    });

// Full API
// mix.js(src, output);
// mix.react(src, output); <-- Identical to mix.js(), but registers React Babel compilation.
// mix.extract(vendorLibs);
// mix.sass(src, output);
// mix.less(src, output);
// mix.stylus(src, output);
// mix.browserSync('my-site.dev');
// mix.combine(files, destination);
// mix.babel(files, destination); <-- Identical to mix.combine(), but also includes Babel compilation.
// mix.copy(from, to);
// mix.copyDirectory(fromDir, toDir);
// mix.minify(file);
// mix.sourceMaps(); // Enable sourcemaps
// mix.version(); // Enable versioning.
// mix.disableNotifications();
// mix.setPublicPath('path/to/public');
// mix.setResourceRoot('prefix/for/resource/locators');
// mix.autoload({}); <-- Will be passed to Webpack's ProvidePlugin.
// mix.webpackConfig({}); <-- Override webpack.config.js, without editing the file directly.
// mix.then(function () {}) <-- Will be triggered each time Webpack finishes building.
// mix.options({
//   extractVueStyles: false, // Extract .vue component styling to file, rather than inline.
//   processCssUrls: true, // Process/optimize relative stylesheet url()'s. Set to false, if you don't want them touched.
//   purifyCss: false, // Remove unused CSS selectors.
//   uglify: {}, // Uglify-specific options. https://webpack.github.io/docs/list-of-plugins.html#uglifyjsplugin
//   postCss: [] // Post-CSS options: https://github.com/postcss/postcss/blob/master/docs/plugins.md
// });
