$(dirname ${0%})/build.sh

# Stuff is copied to a seperate prod location so
# that edits can be made in this dev location
sudo systemctl stop sickle.service
sudo rm -r /home/server/bin/sickle
sudo cp -r . /home/server/bin/sickle
sudo chown -R server:server /home/server/bin/sickle
sudo systemctl restart sickle.service
