#!/bin/bash
cd /data/PearV2
# Remove any empty/broken API_SECRET_KEY lines
sed -i '/^API_SECRET_KEY/d' .env
# Generate and append a new key
KEY=$(openssl rand -hex 32)
echo "API_SECRET_KEY=$KEY" >> .env
echo "Added API_SECRET_KEY=${KEY:0:8}..."
# Restart
pm2 restart pearv2
sleep 5
pm2 logs pearv2 --lines 10 --nostream
