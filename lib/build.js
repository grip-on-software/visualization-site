import structure from 'navbar.spec';
import config from 'config.json';

const build = function(navbar, locales, configuration) {
    var navConfig = Object.assign(config, {
        "container": "#navbar",
        "languages": "#languages"
    }, configuration);
    Object.keys(navConfig).forEach(function(key) {
        if (navConfig[key].replace) {
            navConfig[key] = navConfig[key].replace(/\/?\$organization/,
                navConfig.organization ? `/${navConfig.organization}` : ''
            );
        }
    });
    const nav = new navbar(navConfig, locales);
    nav.fill(structure);
};

window.buildNavigation = build;
window.webpackJsonp = null;

export default build;
