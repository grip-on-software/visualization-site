FROM node:16-alpine
EXPOSE 8080

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ARG NODE_ENV
ENV NODE_ENV $NODE_ENV
ARG NPM_REGISTRY
RUN npm config set @gros:registry $NPM_REGISTRY
COPY package*.json webpack.mix.js /usr/src/app/
RUN apk --update add git && \
	npm install && npm cache clean --force && \
	apk del git && rm -rf /var/cache/apk/*
COPY navbar.json navbar.*.js [c]onfig.json *.conf.mustache /usr/src/app/
COPY caddy/ /usr/src/app/caddy/
COPY lib/ /usr/src/app/lib/
COPY httpd/ /usr/src/app/httpd/
COPY nginx/ /usr/src/app/nginx/
COPY res/ /usr/src/app/res/
COPY template/ /usr/src/app/template/
COPY test/ /usr/src/app/test/

CMD ["npm", "start"]
