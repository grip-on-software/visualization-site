import navbar from './navbar.json';

Array.prototype.last = function() {
    return this[this.length-1];
};

navbar.last().items.last().items.unshift({
    "type": "link",
    "url": "http://blog.gros.example/",
    "icon": ["fas", "rss-square"],
    "content": {
        "en": "Blog",
        "nl": "Blog"
    }
}, {
    "type": "link",
    "url": "http://discussion.gros.example/",
    "icon": ["fab", "discourse"],
    "content": {
        "en": "Discussion",
        "nl": "Discussie"
    }
});
navbar.last().items.last().items.push({
    "type": "image",
    "url": "images/ictu.svg",
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
});

export default navbar;
