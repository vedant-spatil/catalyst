FROM node:22-slim AS build
WORKDIR /app
RUN corepack enable
COPY package.json ./
COPY pnpm-lock.yaml* ./
RUN pnpm install
COPY . .
ARG VITE_API_URL=http://127.0.0.1:4000
ENV VITE_API_URL=$VITE_API_URL
RUN pnpm build
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
