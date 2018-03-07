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
COPY lib/ /usr/src/app/lib/
COPY res/ /usr/src/app/res/
COPY www/ /usr/src/app/www/
RUN npm run production -- --env.mixfile=$PWD/webpack.mix.js 

CMD ["npm", "start"]
