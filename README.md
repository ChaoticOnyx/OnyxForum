Below you can find guidance for local OnyxForum isntallation and configuration for developing purposes.
OnyxForum is based on Flask and FlaskBB, so you can find additional useful information on the link below:

https://flaskbb.readthedocs.io/en/latest/installation.html


# System prerequisites

Required prerequisites:

* git
* python3
* npm
* mysql or any other SQL-compatible DB server

Optional prerequisites:

* redis - required for some queue-based features

One-line command to install prerequisites:

```
sudo apt install git python3 npm redis-server mysql-server
```

Check if mysql and redis are running:

```
systemctl status mysql/redis
```

Run mysql and redis, if they are not:

```
systemctl start mysql/redis
```

Optional, set mysql and redis to start on OS startup:

```
systemctl enable mysql/redis
```


# Setup and start OnyxForum

First of all get sources:

```
cd ~/sources
git clone https://github.com/ChaoticOnyx/OnyxForum
cd OnyxForum
```

Initialize and activate virtual environment:

```
virtualenv .venv --python=python3.8
source .venv/bin/activate
```

Install Python prerequisites:

```
pip install -r requirements.txt
```

Install hub module:

```
pip install -e modules/hub
```
Note: For now, Hub module is required for OnyxForum functioning. It will be decoupled later.

Install DB client python library
Note: If you use other DB server than MySQL (or MariaDB), then you should install corresponding client library, and accordingly configure AlchemySQL on OnyxForum configuration step.

```
sudo apt install libmysqlclient-dev
pip install mysqlclient pymysql
```

Configure Hub module:

`cp modules/hub/hub/configs/example/* modules/hub/hub/configs`
`cp modules/hub/hub/server_config.py.example modules/hub/hub/server_config.py`
Adjust configs at your will

Initialize OnyxForum and gameservers Databases with templates:

```
sudo mysql  # or access mysql console as a local user
mysql> source /[path_to_sources_folder]/OnyxForum/SQL/donations_scheme.sql
mysql> source /[path_to_sources_folder]/OnyxForum/SQL/servers_scheme.sql
```

Start Flask configuration:

```
flaskbb makeconfig --development
```
When wizard is finished, flaskbb.cfg file is created. You can adjust it at your will.

Make some changes to flaskbb.cfg (Note: we configure server for local developing and debugging with simple backend. Settings for release deployment with nginx or another backend will be different):

1. Add 5000 port to url, for example:

`SERVER_NAME = "example.test:5000"`
It's required, because we will configure our debug webserver to forwarding requests for our OnyxForum to 5000 port later.

Add your test domain ("example.test" in the example) to /etc/hosts with redirection to localhost:

```
127.0.0.1 example.test
```

2. Fix SQLALCHEMY_BINDS

Make sure that the names of the hub and gameserver databases are correspond to the names at your DB server.

3. Create Discord bot, fill tokens and DISCORD_REDIRECT_URI

You can create Discord application and bot here: [Developers Applications](https://discord.com/developers/applications)
Guid to python Discord library and bots: [Guide to them](https://discordpy.readthedocs.io/en/stable/discord.html)

* Enable OAUTHLIB_INSECURE_TRANSPORT

```
export OAUTHLIB_INSECURE_TRANSPORT=1
```

Compile themes:

Note: it's may require to install some additional packages with npm
```
cd ./flaskbb/themes/onyx
npm run build:all
# repeat for other themes, that you are going to use
```

* Install the OnyxForum:

```
make install
```

* Finally, run the server:

```
make run
```

# Final configurations

* Change your user's `primary_group_id` in `DB.users` to `1` (Administrators)
* Open your `SERVER_NAME` in browser and log in
* Go to `http://example.test:5000/admin/ -> Plugins -> Portal -> Disable`

Make some more changes to hub's DB:

* Add `ruble` to `onyx -> money_currencies`
* Add `donation` to `onyx -> point_transaction_types`
* Add `other` to `onyx -> point_transaction_types`
* Add `any` to `onyx -> donations_types`
* Add your `discord_id` and `discord_nickname` to `onyx -> dicord_users`
* Add patron type to onyx -> `onyx -> patrons_type`
* Add yourself to `onyx -> players`

# BYOND installation

It's not required for forum usage, but you need to run a gameserver for Hub integration development

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
