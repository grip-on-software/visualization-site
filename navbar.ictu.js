import navbar from './navbar.json';

Array.prototype.last = function() {
    return this[this.length-1];
};

navbar.last().items.last().items.unshift({
    "type": "dropdown",
    "class": "is-focus",
    "link": {
        "url": "mailto:leon.helwerda@ictu.nl",
        "icon": ["fas", "envelope", "xs"],
        "content": {
            "en": "Contact",
            "nl": "Contact"
        }
    },
    "items": [
        {
            "type": "link",
            "url": {"config": "blog_url"},
            "icon": ["fas", "rss-square"],
            "content": {
                "en": "Blog",
                "nl": "Blog"
            }
        },
        {
            "type": "link",
            "url": {"config": "discussion_url"},
            "icon": ["fab", "discourse"],
            "content": {
                "en": "Discussion",
                "nl": "Discussie"
            }
        },
        {
            "type": "link",
            "url": [
                {"config": "jira_url"},
                "/browse/GROS"
            ],
            "title": {
                "en": "View and create issues for GROS",
                "nl": "Taken voor GROS bekijken en maken"
            },
            "icon": ["fas", "chalkboard", "xs"],
            "content": {
                "en": "JIRA",
                "nl": "Jira"
            }
        }
    ]
});
navbar.last().items.last().items.push({
    "type": "link",
    "url": "https://www.ictu.nl",
    "title": {
        "en": "ICTU",
        "nl": "Stichting ICTU"
    },
    "content": [
        {
            "type": "image",
            "url": [
                {"config": "visualization_url"},
                "images/ictu.svg"
            ],
            "title": {
                "en": "ICTU",
                "nl": "ICTU"
            },
            "alt": {
                "en": "ICTU",
                "nl": "ICTU"
            },
            "width": 52,
            "height": 94
        }
    ]
});

export default navbar;
