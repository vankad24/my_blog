#!/bin/sh

set -e

git pull

# read -rp "Enter server name for Nginx: " SERVER_NAME
SERVER_NAME="molo4ko-blog.h4ck.me"
CONFIG_NAME="my_blog.conf"


export SERVER_NAME


if command -v apt >/dev/null 2>&1; then
    echo "Detected apt. Installing packages..."
    
    sudo apt update
    sudo apt install -y nginx certbot python3-certbot-nginx nodejs npm
	sudo systemctl enable --now docker nginx
	
	sed "s/{SERVER_NAME}/$SERVER_NAME/g" nginx-config.template | sudo tee "/etc/nginx/sites-available/$CONFIG_NAME" > /dev/null
	sudo ln -sfn /etc/nginx/sites-available/$CONFIG_NAME /etc/nginx/sites-enabled/$CONFIG_NAME
	sudo systemctl reload nginx
	
elif command -v apk >/dev/null 2>&1; then
    echo "Detected apk. Installing packages..."
    
    sudo apk update
    sudo apk add nginx nginx-systemd certbot certbot-nginx nodejs npm
	sudo systemctl enable --now docker nginx
	
	
	sed "s/{SERVER_NAME}/$SERVER_NAME/g" nginx-config.template | sudo tee "/etc/nginx/http.d/$CONFIG_NAME" > /dev/null
	sudo rm -f /etc/nginx/http.d/default.conf
	sudo systemctl reload nginx

else
    echo "Error: neither apt nor apk was found."
    exit 1
fi

sudo nginx -t && sudo systemctl reload nginx

docker compose down
docker compose up -d --build

# Run in subshell
(cd frontend && npm install && npm run build)

echo "Do you want to update https certificates? (y/n)"
read answer
if [ "$answer" = "y" ]; then
	sudo certbot --nginx -d "$SERVER_NAME"
	sudo certbot renew --dry-run

else
	echo "Skip updating certificates"
fi

echo backend 127.0.0.1:8000
echo pgadmin 127.0.0.1:8080 server connection: host=postgres:5432 username=postgres
echo "To check https try visit: https://$SERVER_NAME"

