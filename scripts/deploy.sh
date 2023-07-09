# Stuff is copied to a seperate prod location so
# that edits can be made in this dev location
#
# To be run as root
if [ "$(whoami)" != "root" ]; then
  echo 'Please run as root'
  exit 255
fi

systemctl stop sickle.service

mv /home/server/prod/sickle-bot/config.py /home/server/tmp/config.py
mv /home/server/prod/sickle-bot/db.json /home/server/tmp/db.json

rm -rf /home/server/prod/sickle-bot
rsync -a --progress . /home/server/prod/sickle-bot --exclude config.py
chown -R server:server /home/server/prod/sickle-bot

mv /home/server/tmp/config.py /home/server/prod/sickle-bot/config.py
mv /home/server/tmp/db.json /home/server/prod/sickle-bot/db.json

# Sensitive files should only be accesible by the user these files are for
chown root:server /home/server/prod/sickle-bot/db.json
chmod 640 /home/server/prod/sickle-bot/db.json
chown root:server /home/server/prod/sickle-bot/db.json
chmod 660 /home/server/prod/sickle-bot/db.json

systemctl start sickle.service
