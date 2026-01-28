FROM node:latest
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm ci --production
COPY . .
ENV PORT=5176
EXPOSE 5176
CMD ["node", "server.js"]
