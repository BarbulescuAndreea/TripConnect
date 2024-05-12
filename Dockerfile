# # Use the official Kong image as the base image
# FROM kong:latest

# # Copy the Kong declarative configuration file into the image
# COPY kong.yml /kong/declarative/kong.yml

# RUN chmod 777 /kong/declarative/kong.yml

# # Set environment variables
# ENV KONG_DATABASE="off"
# ENV KONG_PROXY_LISTEN="0.0.0.0:8000"
# ENV KONG_ADMIN_LISTEN="0.0.0.0:8001"
# ENV KONG_PROXY_ACCESS_LOG="/dev/stdout"
# ENV KONG_ADMIN_ACCESS_LOG="/dev/stdout"
# ENV KONG_PROXY_ERROR_LOG="/dev/stderr"
# ENV KONG_ADMIN_ERROR_LOG="/dev/stderr"
# ENV KONG_DECLARATIVE_CONFIG="/kong/declarative/kong.yml"

# # Expose ports
# EXPOSE 8000 8001

# Use the official Prometheus image as the base image
FROM prom/prometheus

# Copy the Prometheus configuration file into the container
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Set the command to start Prometheus with the custom configuration file
CMD ["--config.file=/etc/prometheus/prometheus.yml"]

# Expose the default Prometheus port
EXPOSE 9090