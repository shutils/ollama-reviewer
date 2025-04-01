FROM node:22-alpine AS build

WORKDIR /app
COPY ../frontend/package*.json ./

RUN npm ci
COPY ../frontend/ ./
RUN npm run build

FROM nginx:1.19.4

COPY --from=build /app/dist /usr/share/nginx/html