FROM node:latest
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm ci --production
COPY . .
ENV PORT=3000
EXPOSE 3000
CMD ["node", "server.js"]
