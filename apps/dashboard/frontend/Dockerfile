FROM node:22-alpine

WORKDIR /app

COPY apps/dashboard/frontend/package*.json /app/
RUN npm ci

COPY apps/dashboard/frontend /app

EXPOSE 5173

CMD ["npm", "run", "dev"]
