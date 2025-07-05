# Stage 1: Build the React application
FROM oven/bun:1 as builder

WORKDIR /app

# Copy package.json and bun.lockb first to leverage Docker cache
COPY package.json bun.lockb ./

# Install dependencies
# Attempt a more forceful clean install
RUN rm -rf node_modules && bun install --frozen-lockfile --verbose

# Copy the rest of the application code
COPY . .

# Set build-time environment variables if needed by Vite for API URLs
# For example, if your app reads VITE_API_BASE_URL from .env
# ARG VITE_API_BASE_URL=/api/v1
# ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
# Ensure your vite.config.ts or api.ts uses this env var for production builds,
# or that the proxy path /api/v1 is correctly handled by the serving mechanism.

# Build the application
RUN bun run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy a custom Nginx configuration if needed (e.g., to handle SPA routing)
# For SPAs, you often need Nginx to redirect all 404s to index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]