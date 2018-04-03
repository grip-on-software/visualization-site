import * as d3 from 'd3';
import feather from 'feather-icons';
import {locale, navbar} from '@gros/visualization-ui';
import spec from './locales.json'
import build from './build';

const locales = new locale(spec);
const searchParams = new URLSearchParams(window.location.search);
locales.select(searchParams.get("lang"));

locales.updateMessages(d3.select('.section'), ['title']);
build(navbar, locales, {});

feather.replace();
