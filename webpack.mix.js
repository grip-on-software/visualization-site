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

let navbar = path.resolve(__dirname, `navbar.${process.env.NAVBAR_SCOPE}.js`);
if (!fs.existsSync(navbar)) {
    navbar = path.resolve(__dirname, 'navbar.json');
}

let configFile = 'config.json',
    config = path.resolve(__dirname, configFile);
if (!fs.existsSync(config)) {
    configFile = 'lib/config.json';
    config = path.resolve(__dirname, configFile);
}
const configuration = JSON.parse(fs.readFileSync(config));
if (process.env.NODE_ENV === 'test') {
    // Always use jenkins proxy URLs in test
    configuration.jenkins_direct = '';
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

// NGINX and Docker-compose service template configuration
const control_host_index = configuration.control_host.indexOf('.');
const domain_index = configuration.visualization_server.indexOf('.');
const internal_domain_index = configuration.jenkins_host.indexOf('.');
const srvConfiguration = _.assign({}, visualizations, _.mapValues(configuration,
    // Remove any organization parameters from URLs
    // The injected branch setter (hub_regex with associated configuration) is
    // not adjusted and is responsible for routing the correct organization(s)
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
    user_id: process.getuid(),
    group_id: process.getgid(),
    visualization_names: visualization_nginx,
    prediction_organizations: _.includes(visualization_names, 'prediction-site') ?
        _.map(configuration.hub_organizations, 'prediction-site') : [],
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
            return '/';
        };
    },
    url: function() {
        return function(text, render) {
            const url_parts = render(text).split('/');
            var server = url_parts.shift();
            return (new URL(url_parts.join('/'), `http://${server}/`))
                .pathname.replace('//', '/');
        };
    },
    upstream: function() {
        return function(text, render) {
            return `$${text}`;
        };
    },
    jenkins_report: function() {
        return function(text, render) {
            const url_parts = render(text).split('/');
            const job = url_parts.shift();
            const branch = url_parts.shift();
            const file = url_parts.join('/');
            if (configuration.jenkins_direct) {
                return `${configuration.jenkins_direct}/${branch}/${job}/${file}`;
            }
            return `${configuration.jenkins_path}/job/build-${job}/job/${branch}/Visualization/${file}`;
        };
    },
    jenkins_artifact: function() {
        return function(text, render) {
            const url_parts = render(text).split('/');
            const job = url_parts.shift();
            const branch = url_parts.shift();
            const file = url_parts.join('/');
            if (configuration.jenkins_direct) {
                return `${configuration.jenkins_direct}/${branch}/${job}/${file}`;
            }
            return `${configuration.jenkins_path}/job/create-${job}/job/${branch}/lastSuccessfulBuild/artifact/${file}`;
        };
    },
    jenkins_branches: configuration.jenkins_direct ?
        `${configuration.jenkins_direct}/branches.json` :
        `${configuration.jenkins_path}/job/create-prediction/api/json?tree=jobs[name,color,lastSuccessfulBuild[timestamp]]`,
    error_log: process.env.NODE_ENV === 'test' ? 'notice' : 'error',
    rewrite_log: process.env.NODE_ENV === 'test' ? 'on' : 'off'
});

const templates = [
    'nginx.conf', 'nginx/blog.conf', 'nginx/discussion.conf',
    'nginx/prediction.conf', 'nginx/visualization.conf', 'nginx/websocket.conf',
    'caddy/docker-compose.yml', 'test/docker-compose.yml'
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
        throw new Error(`Could not render ${template}.mustache: ${e.message}`);
    }
});

// Generate configuration to import into the navbar builder
const jsConfiguration = _.assign({}, _.pickBy(configuration,
    (value, key) => key.endsWith('_url')
), {
    organization:
    typeof process.env.VISUALIZATION_ORGANIZATION !== 'undefined' ?
    process.env.VISUALIZATION_ORGANIZATION : ''
});
const configAlias = path.resolve(__dirname, 'config-alias.json');
fs.writeFileSync(configAlias, JSON.stringify(jsConfiguration));

// Generage configuration for HTML pages
const htmlConfiguration = _.assign({}, urlConfiguration, messages,
    visualizations
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
