/**
 * Common navigation bar builder for visualizations within the hub.
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
import structure from 'navbar.spec';
import config from 'config.json';

const breakpoint = '(min-width: 1024px)';

const alterOrganizationItem = (accumulator, item, visualization, navbar, navConfig, locales) => {
    if (!navConfig.visualization) {
        accumulator.push(item);
        return;
    }

    const org = item.id.substring(13); // 'organization-'.length
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
};

const updateDropdownLinks = () => {
    const dropdown = '.has-dropdown.is-hoverable';
    const updateLink = function(event) {
        const isTouch = window.matchMedia('(hover: none)').matches;
        if (event.type === 'blur') {
            if (!isTouch) {
                this.parentNode.classList.remove('is-active');
            }
        }
        else {
            this.parentNode.classList.toggle('is-active');
            if (isTouch || this.parentNode.classList.contains('is-focus')) {
                event.preventDefault();
            }
        }
    };
    document.querySelectorAll(`.navbar ${dropdown} .navbar-link`)
        .forEach((link) => {
            // Make external links open in new tab/window if we do click on them
            if (link.classList.contains('is-external')) {
                link.setAttribute('target', '_blank');
            }
            link.addEventListener('click', updateLink);
            link.addEventListener('blur', updateLink);
        });
    const updateDropdowns = (query) => {
        document.querySelectorAll(`.navbar .is-active, .navbar ${dropdown}`).forEach((item) => {
            if (query.matches) {
                item.classList.remove('is-active');
            }
            else {
                item.classList.add('is-active');
            }
        });
    };
    const media = window.matchMedia(breakpoint);
    updateDropdowns(media);
    media.addEventListener('change', (event) => {
        updateDropdowns(event);
    });
};

const build = function(navbar, locales, configuration) {
    // Prioritize our own configuration defaults and element structure over
    // the visualization's preferences, including URLs that may or may not have
    // the $organization variable in them.
    let navConfig = Object.assign({visualization: ""}, configuration, {
        container: "#navbar",
        languages: "#languages",
        visualizations: {}
    }, config);

    // Alter the navigation bar structure to make the current visualization
    // active and to change organization switcher to link to specific
    // visualization URLs, and remove switcher options if no other organization
    // provides this visualization (or only one organization is configured).
    let visualization = {};
    const visualizationMap = (accumulator, item) => {
        // Link type
        if (item.id === `visualization-${navConfig.visualization}`) {
            item.class = "item is-active";
            visualization = item;
            accumulator.push(item);
            return accumulator;
        }
        if (typeof item.id === "string" && item.id.startsWith('organization-')) {
            alterOrganizationItem(accumulator, item, visualization, navbar,
                navConfig, locales
            );
            return accumulator;
        }
        // Dropdown type (but also menu and brand are reduced)
        if (item.items) {
            item.items = item.items.reduce(visualizationMap, []);
            if (item.id === "organizations" && item.items.length === 1) {
                const content = item.items[0].content;
                item = item.link;
                item.type = "link";
                item.class = "link is-arrowless is-external";
                item.title = content;
            }
        }
        accumulator.push(item);
        return accumulator;
    };
    const navStructure = structure.reduce(visualizationMap, []);

    // Adjust configuration for actual structure with current organization in
    // the URLs to replace links with.
    const org = navConfig.organization ? `/${navConfig.organization}` : '';
    Object.keys(navConfig).forEach(function(key) {
        if (key.endsWith('_url')) {
            navConfig[key] = navConfig[key].replace(/\/?\$organization/, org);
        }
    });
    navConfig.base_url = new URL(navConfig.visualization === "prediction" ?
        navConfig.prediction_url :
        `${navConfig.visualization_url}${navConfig.visualization}`,
        navConfig.base_url || document.location
    ).href;
    const nav = new navbar(navConfig, locales);
    nav.fill(navStructure);
    updateDropdownLinks();
};

window.buildNavigation = build;
window.webpackJsonp = null;

export default build;
