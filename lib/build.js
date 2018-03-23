import structure from 'navbar.spec';
import config from 'config.json';

const build = function(navbar, locales, configuration) {
    const navConfig = Object.assign(config, {
        "container": "#navbar",
        "languages": "#languages"
    }, configuration);
    const nav = new navbar(navConfig, locales);
    nav.fill(structure);
};

export default build;
