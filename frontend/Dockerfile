# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker cache
COPY ./frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY ./frontend /app
COPY ../.env /app/.env

# Build the app
RUN npm run build

# Install a static server to serve the build folder
RUN npm install -g serve

# Command to run the app
CMD ["serve", "-s", "build", "-l", "3000"]