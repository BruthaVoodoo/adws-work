FROM node:20-slim
WORKDIR /usr/src/app
COPY package*.json ./
# Install all dependencies (including devDependencies like vite/rollup)
RUN npm ci
COPY . .
ENV PORT=5173
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
