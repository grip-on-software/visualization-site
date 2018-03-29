let fs = require('fs'),
    mix = require('laravel-mix');
const HtmlWebpackPlugin = require('html-webpack-plugin');

let navbar = path.resolve(__dirname, `navbar.${process.env.NAVBAR_SCOPE}.js`);
if (!fs.existsSync(navbar)) {
    navbar = path.resolve(__dirname, 'navbar.json');
}

let config = path.resolve(__dirname, 'config.json');
if (!fs.existsSync(config)) {
    config = path.resolve(__dirname, 'lib/config.json');
}
const configuration = JSON.parse(fs.readFileSync(config));

Mix.paths.setRootPath(__dirname);
mix.setPublicPath('www/')
    .setResourceRoot(process.env.BRANCH_NAME !== 'master' ? '/' : configuration.visualization_url)
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
            publicPath: process.env.BRANCH_NAME !== 'master' ? '.' : configuration.visualization_url
        },
        module: {
            rules: [ {
                test: /\.mustache$/,
                loader: 'mustache-loader',
                options: {
                    tiny: true,
                    render: Object.assign({}, JSON.parse(fs.readFileSync(config)))
                }
            } ]
        },
        plugins: [
            new HtmlWebpackPlugin({
                template: 'template/index.mustache',
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
                'config.json$': config
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
