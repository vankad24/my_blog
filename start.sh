#!/bin/bash

set -e

if command -v apt >/dev/null 2>&1; then
    echo "Detected apt. Installing packages..."
    
    sudo apt update
    sudo apt install -y nginx certbot python3-certbot-nginx

elif command -v apk >/dev/null 2>&1; then
    echo "Detected apk. Installing packages..."
    
    sudo apk update
    sudo apk add nginx certbot certbot-nginx

else
    echo "Error: neither apt nor apk was found."
    exit 1
fi


# read -rp "Enter server name for Nginx: " SERVER_NAME
SERVER_NAME="molo4ko-blog.h4ck.me"
PROJECT_NAME="my_blog"

export SERVER_NAME

sed "s/{SERVER_NAME}/$SERVER_NAME/g" nginx-config.template > "/etc/nginx/sites-available/$PROJECT_NAME"
sudo ln -s /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/$PROJECT_NAME

sudo nginx -t && sudo systemctl reload nginx

docker compose up -d --build

sudo certbot --nginx -d "$SERVER_NAME"

sudo certbot renew --dry-run

echo "Try visit: https://$SERVER_NAME"