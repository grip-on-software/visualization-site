import * as d3 from 'd3';
import feather from 'feather-icons';
import {locale, navbar} from '@gros/visualization-ui';
import build from './build';

const locales = new locale({
    "en": {"language": "English"},
    "nl": {"language": "Nederlands"}
});
const searchParams = new URLSearchParams(window.location.search);
locales.select(searchParams.get("lang"));

build(navbar, locales, {});

feather.replace();
