FROM node:8
EXPOSE 8080

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ARG NODE_ENV
ENV NODE_ENV $NODE_ENV
ARG NPM_REGISTRY
RUN npm config set @gros:registry $NPM_REGISTRY
COPY package.json webpack.mix.js /usr/src/app/
RUN npm install && npm cache clean --force
COPY navbar.json navbar.*.js [c]onfig.json nginx.conf.mustache /usr/src/app/
COPY caddy/ /usr/src/app/caddy/
COPY lib/ /usr/src/app/lib/
COPY nginx/ /usr/src/app/nginx/
COPY res/ /usr/src/app/res/
COPY template/ /usr/src/app/template/
COPY test/ /usr/src/app/test/
ARG NAVBAR_SCOPE
ARG BRANCH_NAME

CMD ["npm", "start"]
