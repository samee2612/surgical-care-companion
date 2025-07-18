FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Set environment variable for NODE_ENV
ENV NODE_ENV=development

# Expose port
EXPOSE 5000

# Start server directly with node using --import
CMD ["node", "--import", "tsx/esm", "server/index.ts"]
