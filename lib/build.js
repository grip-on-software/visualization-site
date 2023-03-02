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
    let navConfig = Object.assign(config, {
        "container": "#navbar",
        "languages": "#languages"
    }, configuration);
    let navStructure = structure;
    let visualization = {};
    if (navConfig.visualization) {
        const visualizationMap = (accumulator, item) => {
            if (!item.type) {
                accumulator.push(item);
                return accumulator;
            }
            if (item.type === "dropdown" && item.id !== "visualizations" &&
                item.id !== "organizations"
            ) {
                accumulator.push(item);
                return accumulator;
            }
            if (item.type === "link" && typeof item.id !== "undefined") {
                if (item.id === `visualization-${navConfig.visualization}`) {
                    item.class = "item is-active";
                    visualization = item;
                    accumulator.push(item);
                }
                else if (item.id.startsWith('organization-')) {
                    const org = item.id.substring(13); // 'organization-'
                    if (!navConfig.visualizations[org] ||
                        navConfig.visualizations[org].includes(
                            navConfig.visualization
                        )
                    ) {
                        let url = visualization.url ? visualization.url : [
                            {config: "visualization_url"},
                            navConfig.visualization,
                            "?lang=",
                            {"locale": "lang"}
                        ];
                        const nav = new navbar(navConfig, locales);
                        url = nav.link(url);
                        item.url = url.replace(/\/?\$organization/, `/${org}`);
                        accumulator.push(item);
                    }
                }
                else {
                    accumulator.push(item);
                }
                return accumulator;
            }
            if (item.items) {
                item.items = item.items.reduce(visualizationMap, []);
                if (item.type === "dropdown" && item.id === "organizations" &&
                    item.items.length === 1
                ) {
                    const content = item.items[0].content;
                    item = item.link;
                    item.type = "link";
                    item.title = content;
                }
            }
            accumulator.push(item);
            return accumulator;
        };
        navStructure = structure.reduce(visualizationMap, []);
    }

    Object.keys(navConfig).forEach(function(key) {
        if (navConfig[key].replace) {
            navConfig[key] = navConfig[key].replace(/\/?\$organization/,
                navConfig.organization ? `/${navConfig.organization}` : ''
            );
        }
    });
    const nav = new navbar(navConfig, locales);
    nav.fill(navStructure);

    document.querySelectorAll('.navbar .has-dropdown .navbar-link.is-external')
        .forEach((link) => {
            link.addEventListener('click', (event) => {
                event.preventDefault();
                window.open(link.href, '_blank');
            });
        });
};

window.buildNavigation = build;
window.webpackJsonp = null;

export default build;
