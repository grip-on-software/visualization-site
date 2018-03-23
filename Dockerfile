FROM node:6
EXPOSE 8080

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ARG NODE_ENV
ENV NODE_ENV $NODE_ENV
ARG NPM_REGISTRY
RUN npm config set @gros:registry $NPM_REGISTRY
COPY package.json webpack.mix.js /usr/src/app/
RUN npm install && npm cache clean --force
COPY navbar.json navbar.*.js [c]onfig.json /usr/src/app/
COPY lib/ /usr/src/app/lib/
COPY res/ /usr/src/app/res/
COPY template /usr/src/app/template/
COPY www/ /usr/src/app/www/
ARG NAVBAR_SCOPE
RUN npm run production -- --env.mixfile=$PWD/webpack.mix.js --env.NAVBAR_SCOPE=$NAVBAR_SCOPE

CMD ["npm", "start"]
