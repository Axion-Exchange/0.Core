cd /data/PearV2
sed -i '/^API_SECRET_KEY/d' .env
KEY=$(openssl rand -hex 32)
echo "API_SECRET_KEY=$KEY" >> .env
grep API_SECRET_KEY .env
pm2 restart pearv2
sleep 5
pm2 logs pearv2 --lines 10 --nostream