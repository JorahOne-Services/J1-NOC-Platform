# =============================================================================
# J1-NOC-Platform Frontend — React + Vite → nginx
# Tag convention: jorahone/jnop-frontend:latest
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./
RUN npm ci --include=dev

# Copy source and build
COPY . .
RUN npm run build

# ── Production stage ────────────────────────────────────────────────────────
FROM nginx:1.30.3-alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user for nginx
RUN addgroup --system --gid 1001 jnop && \
    adduser --system --uid 1001 --ingroup jnop --no-create-home jnop && \
    chown -R jnop:jnop /usr/share/nginx/html /var/cache/nginx /tmp && \
    chmod -R 755 /usr/share/nginx/html && \
    chmod 1777 /tmp

# nginx writes its pid file at startup; redirect it to /tmp so the non-root
# user can write it (otherwise open("/run/nginx.pid") fails with EACCES and
# the container crash-loops). Also drop the root-only `user` directive.
RUN sed -i 's#/run/nginx.pid#/tmp/nginx.pid#g' /etc/nginx/nginx.conf && \
    sed -i '/^user[[:space:]]/d' /etc/nginx/nginx.conf

USER jnop

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD wget --spider -q http://127.0.0.1/ || exit 1

LABEL org.opencontainers.image.title="J1-NOC-Platform Frontend" \
      org.opencontainers.image.description="React + Vite frontend for J1 NOC Platform" \
      org.opencontainers.image.vendor="JorahOne" \
      org.opencontainers.image.version="1.0.0"

CMD ["nginx", "-g", "daemon off;"]
