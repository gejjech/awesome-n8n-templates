FROM nginx:1.27-alpine

# Build args (optional): APP_DIST defaults to /usr/share/nginx/html
ARG APP_DIST=/usr/share/nginx/html

# Copy static site from dist/ (expected prebuilt) into nginx html
COPY dist/ ${APP_DIST}

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost/ >/dev/null || exit 1

