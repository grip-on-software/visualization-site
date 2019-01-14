import * as d3 from 'd3';
import feather from 'feather-icons';
import {Locale, Navbar} from '@gros/visualization-ui';
import spec from './locales.json';
import build from './build';

const locales = new Locale(spec);
const searchParams = new URLSearchParams(window.location.search);
locales.select(searchParams.get("lang"));

locales.updateMessages(d3.select('.section'), ['title'], null);
build(Navbar, locales, {});

feather.replace();

d3.selectAll('[data-language]').each(function() {
    const link = d3.select(this);
    const url = new URL(link.attr('href'), window.location);
    const param = link.attr('data-language');
    url.search = url.search + (url.search === '' ? '?' : '&') +
        (param === '' ? '' : param + '=') + locales.lang;
    link.attr('href', url);
});
