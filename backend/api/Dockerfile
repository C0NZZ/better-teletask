FROM node:22

WORKDIR /node

COPY package-lock.json package.json ./

RUN npm install

COPY database.js index.js ./

CMD [ "index.js" ]