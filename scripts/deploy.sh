$(dirname ${0%})/build.sh

# Stuff is copied to a seperate prod location so
# that edits can be made in this dev location
#
# To be run as root
systemctl stop sickle.service
rm -rf /home/server/prod/sickle-bot
rsync -av --progress . /home/server/prod/sickle-bot --exclude config.py
chown -R server:server /home/server/prod/sickle-bot
systemctl start sickle.service
