const fs = require('fs'),
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

// Replace organization parameter with environment variable if necessary.
// Used for visualization links and HTML configuration
const urlConfiguration = _.mapValues(configuration,
    (value, key) => {
        if (!key.endsWith('_url')) {
            return value;
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
        items: _.map(group.items, (item) => _.assign({}, item, {
            show: typeof item.url !== "undefined" ?
                mustache.render(item.url, urlConfiguration) : item.id,
            download: typeof item.download !== "undefined" ?
                mustache.render(item.download, urlConfiguration) :
                `${item.id}.zip`,
            icon: `<span class="icon">
                <i class="${_.map(item.icon, (part, i) => i === 0 ? part : `fa-${part}`).join(' ')}" aria-hidden="true"></i>
            </span>`,
            title: message(`${item.id}-title`),
            content: message(`${item.id}-content`)
        }))
    })
);
const visualization_names = _.flattenDeep(_.map(visualizations.groups,
    (group) => _.map(group.items, (item) => item.skip_test ? [] : item.id)
));
fs.writeFileSync(path.resolve(__dirname, 'visualization_names.txt'),
    visualization_names.join(' ')
);

// NGINX template configuration
const control_host_index = configuration.control_host.indexOf('.');
const domain_index = configuration.visualization_server.indexOf('.');
const internal_domain_index = configuration.jenkins_host.indexOf('.');
const nginxConfiguration = _.assign({}, _.mapValues(configuration,
    // Remove any organization parameters from URLs (not injected branch setter)
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
    visualization_names: visualization_names,
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
                nginxConfiguration
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
const htmlConfiguration = _.assign({}, urlConfiguration, messages, {
    visualization_names: visualization_names,
    groups: visualizations.groups
});

Mix.paths.setRootPath(__dirname);
mix.setPublicPath('www/')
    .setResourceRoot(process.env.BRANCH_NAME.endsWith('master') ? htmlConfiguration.visualization_url : '/')
    .js('lib/index.js', 'www/bundle.js')
    .extract(['./lib/build.js'])
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
            publicPath: process.env.BRANCH_NAME.endsWith('master') ? htmlConfiguration.visualization_url : '.'
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
                inject: false
            }),
            new HtmlWebpackPlugin({
                template: 'template/403.mustache',
                filename: '403.html',
                inject: false
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
