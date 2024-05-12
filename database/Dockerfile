# Use the official PostgreSQL image from Docker Hub
FROM postgres:latest

# Set environment variables
ENV POSTGRES_USER=apple \
    POSTGRES_PASSWORD=0000 \
    POSTGRES_DB=trip_connect

# Copy the SQL initialization script to the container
COPY ./tables-db.sql /docker-entrypoint-initdb.d/tables-db.sql

# Expose PostgreSQL port (not mandatory in this case as it's handled by the service definition)
EXPOSE 5432