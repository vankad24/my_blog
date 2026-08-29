#!/bin/bash

sudo apt update
sudo apt install nginx certbot certificates python3-certbot-nginx


# read -rp "Enter server name for Nginx: " SERVER_NAME
SERVER_NAME="blog.ru"
PROJECT_NAME="my_blog"

export SERVER_NAME

sed "s/{SERVER_NAME}/$SERVER_NAME/g" nginx-config.template > "/etc/nginx/sites-available/$PROJECT_NAME"
sudo ln -s /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/$PROJECT_NAME

sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d "$SERVER_NAME"

sudo certbot renew --dry-run

docker compose up -d --build

echo "Try visit: https://$SERVER_NAME"