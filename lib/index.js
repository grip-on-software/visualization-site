import * as d3 from 'd3';
import feather from 'feather-icons';
import navbar from './navbar';
import structure from 'navbar.spec';
import config from 'config.json';
import {locale} from '@gros/visualization-ui';

const locales = new locale({
    "en": {"language": "English"},
    "nl": {"language": "Nederlands"}
});
const searchParams = new URLSearchParams(window.location.search);
locales.select(searchParams.get("lang"));

const nav = new navbar(config, locales);
d3.select('#navbar').html(nav.build(structure));

const languages = d3.select('#languages');
locales.generateNavigation(languages, '', 'lang');
languages.select('.is-active').select('a').classed('is-active', true);
languages.selectAll('a').classed('navbar-item', true);

feather.replace();
