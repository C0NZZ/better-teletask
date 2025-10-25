FROM node:22

WORKDIR /node

COPY database.js index.js package-lock.json package.json ./

RUN npm install

CMD [ "index.js" ]

