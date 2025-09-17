# FROM node:lts-alpine as build-stage

# WORKDIR /app

# COPY . .

# RUN npm install

# RUN npm run build --legacy-peer-deps

# # production stage

# FROM nginx:stable as production-stage

# COPY --from=build-stage /app/dist/my-app /var/www/

# RUN rm /etc/nginx/conf.d/default.conf

# COPY ./nginx.conf /etc/nginx/conf.d/default.conf
FROM node:18-alpine AS build

WORKDIR /app

COPY . .

RUN npm install

RUN npm run build

# Serve Application using Nginx Server

FROM nginx:alpine

COPY --from=build /app/dist/frontend/browser/ /usr/share/nginx/html

EXPOSE 80
