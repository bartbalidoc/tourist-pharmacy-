# Tourist Pharmacy — review server, containerised.
# Multi-stage: build the ~3,500-page Astro site, then run the tiny Express server
# (server.mjs) that serves it behind the login + collects feedback. Keeps the host
# clean (no Node/npm installed on the droplet) and fully isolated from other apps.

# --- build stage: produce dist/ ---------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- run stage: serve dist/ via the Express review server -------------------
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
# express lives in dependencies; reuse the resolved modules from the build stage.
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY server.mjs package.json ./
EXPOSE 8080
CMD ["node", "server.mjs"]
