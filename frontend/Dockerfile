# =============================================================================
# NexusCore Frontend — React + Vite → nginx
# Tag convention: jorahone/jnop-frontend:latest
# =============================================================================
FROM node:26-alpine AS builder

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
    chown -R jnop:jnop /usr/share/nginx/html /var/cache/nginx /var/run && \
    chmod -R 755 /usr/share/nginx/html

USER jnop

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD wget --spider -q http://127.0.0.1/ || exit 1

LABEL org.opencontainers.image.title="NexusCore Frontend" \
      org.opencontainers.image.description="React + Vite frontend for J1 NOC Platform" \
      org.opencontainers.image.vendor="JorahOne" \
      org.opencontainers.image.version="1.0.0"

CMD ["nginx", "-g", "daemon off;"]
