#!/bin/sh
# Replace the placeholder with the actual backend URL
# We use a temporary file to avoid empty files if envsubst fails
envsubst '$BACKEND_URL' < /usr/share/nginx/html/index.html.template > /usr/share/nginx/html/index.html

# Start Nginx
exec nginx -g "daemon off;"
