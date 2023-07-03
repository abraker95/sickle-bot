$(dirname ${0%})/build.sh

# Stuff is copied to a seperate prod location so
# that edits can be made in this dev location
#
# To be run as root
systemctl stop sickle.service
mv /home/server/prod/sickle-bot/config.py /home/server/tmp/config.py
mv /home/server/prod/sickle-bot/db.json /home/server/tmp/db.json
rm -rf /home/server/prod/sickle-bot
rsync -av --progress . /home/server/prod/sickle-bot --exclude config.py
chown -R server:server /home/server/prod/sickle-bot
mv /home/server/tmp/config.py /home/server/prod/sickle-bot/config.py
mv /home/server/tmp/db.json /home/server/prod/sickle-bot/db.json
systemctl start sickle.service
