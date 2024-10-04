#!/bin/bash
set -e


# Stuff is copied to a seperate prod location so
# that edits can be made in this dev location
#
# To be run as root
if [ "$(whoami)" != "root" ]; then
  echo 'Please run as root'
  exit 255
fi

systemctl stop sickle.service

# Move config and db files to a temporary location because they would be overwritten otherwise
mv /home/server/prod/sickle-bot/config.yaml /home/server/tmp/config.yaml
mv /home/server/prod/sickle-bot/db.json /home/server/tmp/db.json

# Nuke the folder and copy over the updated files in repo location -> prod location
rm -rf /home/server/prod/sickle-bot
rsync -a --progress . /home/server/prod/sickle-bot --exclude config.yaml --exclude db.json --exclude .git
chown -R server:server /home/server/prod/sickle-bot

# Move config and db files back
mv /home/server/tmp/config.yaml /home/server/prod/sickle-bot/config.yaml
mv /home/server/tmp/db.json /home/server/prod/sickle-bot/db.json

# Sensitive files should only be accesible by the user these files are for
# config: r--r-----
# db:     rw-rw----
chown root:server /home/server/prod/sickle-bot/config.yaml
chmod 440 /home/server/prod/sickle-bot/config.yaml
chown root:server /home/server/prod/sickle-bot/db.json
chmod 660 /home/server/prod/sickle-bot/db.json

chmod +x /home/server/prod/sickle-bot/scripts/run.sh

systemctl start sickle.service
