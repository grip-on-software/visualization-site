import * as d3 from 'd3';
import _ from 'lodash';
import mustache from 'mustache';

const html = (data) => {
    return data !== undefined ? mustache.escape(data) : '';
};
class navbar {
    constructor(config, locales) {
        this.config = config;
        this.locales = locales;
        this.types = {
            "brand": (item) => `
                <div class="navbar-brand">
                    ${this.build(item.items)}
                </div>`,
            "link": (item) => `
                <a class="navbar-${item.class || "item"}"
                    href="${html(this.link(item.url))}"
                    title="${html(this.locale(item.title))}">
                    ${this.icon(item.icon)}
                    ${this.build(item.content)}
                </a>`,
            "image": (item) => `
                <img src="${html(item.url)}" alt="${html(this.locale(item.alt))}"
                    width="${html(item.width)}" height="${html(item.height)}"
                    style="${html(item.style)}">`,
            "text": (item) => `${html(this.locale(item.text))}`,
            "burger": (item) => `
                <div class="navbar-burger" data-target="${html(item.target)}">
                    ${"<span></span>".repeat(item.lines)}
                </div>`,
            "menu": (item) => `
                <div class="navbar-menu" id="${html(item.menu)}">
                    ${this.build(item.items)}
                </div>`,
            "start": (item) => `
                <div class="navbar-start">
                    ${this.build(item.items)}
                </div>`,
            "end": (item) => `
                <div class="navbar-end">
                    ${this.build(item.items)}
                </div>`,
            "dropdown": (item) => `
                <div class="navbar-item has-dropdown is-hoverable">
                    ${this.build([_.assign({"type": "link", "class": "link"}, item.link)])}
                    <div class="navbar-dropdown is-boxed" ${item.id !== undefined ? `id="${html(item.id)}"` : ''}>
                        ${this.build(item.items)}
                    </div>
                </div>`,
            "divider": (item) => `<hr class="navbar-divider">`
        };
    }

    locale(data) {
        if (typeof data === "string" || data === undefined) {
            return data;
        }
        return this.locales.retrieve(data, null, data.en);
    }

    link(data) {
        if (typeof data === "object") {
            return this.config[data.config];
        }
        return data;
    }

    icon(data) {
        if (data === undefined) {
            return '';
        }
        return `<span class="icon">
            <i class="${data[0]} fa-${data[1]}" aria-hidden="true"></i>
        </span>`;
    }

    build(structure) {
        if (typeof structure === "object" && !Array.isArray(structure)) {
            return html(this.locale(structure));
        }
        const nav = this;
        return _.map(structure, (item) => {
            return (nav.types[item.type] || ((item) => {
                console.log(`Invalid type: ${item.type}\n${item}`);
                return '';
            }))(item);
        }).join('\n');
    }
}

export default navbar;
