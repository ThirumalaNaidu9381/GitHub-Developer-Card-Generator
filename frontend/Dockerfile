FROM nginx:alpine

# Copy the HTML file as a template
COPY index.html /usr/share/nginx/html/index.html.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /docker-entrypoint.sh

# Default environment variable
ENV BACKEND_URL=http://localhost:8080

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
