FROM node:20.18.0-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/index.html frontend/tsconfig.json frontend/vite.config.ts frontend/tailwind.config.js frontend/postcss.config.js ./
COPY frontend/public ./public
COPY frontend/src ./src
RUN npm run build

FROM nginx:1.27.3-alpine
RUN rm -f /etc/nginx/conf.d/default.conf && \
    mkdir -p /var/cache/nginx /var/log/nginx /tmp/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx /tmp/nginx /etc/nginx/conf.d
COPY docker/proxy/nginx.conf /etc/nginx/conf.d/sajona_core.conf
COPY --from=builder /app/dist /usr/share/nginx/html
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    sed -i 's|pid .*|pid /tmp/nginx/nginx.pid;|g' /etc/nginx/nginx.conf && \
    sed -i '/^user /d' /etc/nginx/nginx.conf

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/health || exit 1
