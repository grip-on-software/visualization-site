/**
 * Common navigation bar builder for visualizations within the hub.
 *
 * Copyright 2017-2020 ICTU
 * Copyright 2017-2022 Leiden University
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
