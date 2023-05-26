/**
 * Main entry point for the visualization site hub.
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
import * as d3 from 'd3';
import {Locale, Navbar} from '@gros/visualization-ui';
import spec from './locales.json';
import build from './build';

const locales = new Locale(spec);
const searchParams = new URLSearchParams(window.location.search);
locales.select(searchParams.get("lang"));

locales.updateMessages();
locales.updateMessages(d3.select('.section'), ['title', 'aria-label'], null);
build(Navbar, locales, {});

d3.selectAll('[data-language]').each(function() {
    const link = d3.select(this);
    const url = new URL(link.attr('href'), window.location);
    const param = link.attr('data-language');
    url.search = url.search + (url.search === '' ? '?' : '&') +
        (param === '' ? '' : `${param}=`) + locales.lang;
    link.attr('href', url);
});
