FROM node:24

WORKDIR /node

COPY package-lock.json package.json tsconfig.json ./

RUN npm ci

COPY database.ts index.ts ./

RUN npm run build

CMD [ "node", "dist/index.js" ]