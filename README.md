# Installing and starting forum

* Install git, pip and npm if you don't have it:
`sudo apt install git pip npm`

* Install nginx, redis, virtualenvwrapper, mysql(can be changed), celery:
`sudo apt install nginx redis virtualenvwrapper python3-sql celery`

* Compile and install python3.8.13(if we don't fix some bugs):
```
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
wget https://www.python.org/ftp/python/3.8.13/Python-3.8.13.tgz
tar -xf Python-3.8.13.tgz
cd Python-3.8.13
./configure --enable-optimizations
make -j <number of CPU cores>
sudo make altinstall
cd ..
```

* Create virtualenv with python 3.8.13:
`python3.8 -m venv .venv`
or
`virtualenv .venv --python=python3.8`
Activate it:
`source .venv/bin/activate`
* Upgrade pip, wheel and setuptools for venv:
`pip install --upgrade pip wheel setuptools`
* If you don't clone repo it's time to do it

```
git clone https://github.com/ChaoticOnyx/OnyxForum
cd OnyxForum
```
* Install dependencies, dev or not decide you:
`pip install -r requirements.txt`
* Install hub module
`pip install -e modules/hub`
* Install mysqldb
```
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```
* Extract hub.cfg from example
`cp modules/hub/hub/configs/example/* modules/hub/hub/configs`
* Fill it



* Create SQL DB from two templates(check SQL folder)

* Make devconfig(make it default):
`make devconfig`

* Open your `flaskbb.cfg` edit

`SERVER_NAME = "example.test:5000"`

P.S. you can change `example.test` for any host on your PC and don't forget to write it into /etc/hosts

Edit your DB address and replace `"server"`

* Make your discord bot and replace placeholders in `flaskbb.cfg` at the EOF
	[Developers Applications](https://discord.com/developers/applications)
	[Guide to them](https://discordpy.readthedocs.io/en/stable/discord.html)
	Add redirect to your DISCORD_REDIRECT_URI

* Enable OAUTHLIB_INSECURE_TRANSPORT
`export OAUTHLIB_INSECURE_TRANSPORT=1`

* Compile themes
```
cd ./flaskbb/themes/onyx && sudo npm run build:all
```

### Starting this monster:
For first start write:
```
make install
make run
```
For any later starts write:
`make run`

* Change your `primary_group_id` in `flaskbb.sqlite -> users` to `1`
* Go to your `SERVER_NAME` and log in
* Go to `http://example.test:5000/admin/ -> Plugins -> Portal -> Disable`

# DB setup
* Add `ruble` to `onyx -> money_currencies`
* Add `donation` to `onyx -> point_transaction_types`
* Add `other` to `onyx -> point_transaction_types`
* Add `any` to `onyx -> donations_types`
* Add your `discord_id` and `discord_nickname` to `onyx -> dicord_users`
* Add patron type to onyx -> `onyx -> patrons_type`
* Add yourself to `onyx -> players`

# BYOND setup
* [Download BYOND](http://www.byond.com/download/)
* Unzip it where you want
* `sudo make install`

* Git clone our build
* `git clone https://github.com/ChaoticOnyx/OnyxBay`
* Compile it:
* `~/byond/bin/DreamMaker ~/OnyxBay/baystation12.dme`
`touch /etc/systemd/system/onyx.service`

```
[Unit]
Description=Onyx SS13 Server
[Service]
Type=simple
User=[change to current user]
Restart=always
RestartSec=10
ExecStart=/home/user/byond/bin/DreamDaemon /home/user/OnyxBay/baystation12.dmb 2505 -trusted -core -invisible
WorkingDirectory=/home/user/OnyxBay
```
### Dont forget to change directories

* Restart daemon
`systemctl daemon-reload`

* Rename example of servers config `modules/hub/hub/servers_config.py.example` -> `modules/hub/hub/servers_config.py`
* Redact it with your needs

# Misc

* For hub log
**Don't forget change <server_id>**
```
mkdir logs/<serverd_id>
touch logs/<serverd_id>/update.log
touch logs/<serverd_id>/server.log
```
