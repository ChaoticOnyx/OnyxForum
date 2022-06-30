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

```
SQLALCHEMY_DATABASE_URI = "sqlite:////home/zero/OnyxForum/flaskbb.sqlite"
SQLALCHEMY_BINDS = {
    "hub": "mysql://username:password@localhost/onyx?charset=utf8mb4",
    "chaotic": "mysql://username:password@localhost/chaotic?charset=utf8mb4"
}
```


`PREFERRED_URL_SCHEME = "https"`

```
# Don't send secure cookies over an unencrypted connection ()
SESSION_COOKIE_SECURE = False
# Don't make cookies available to JS (XSS) - browsers hide httpOnly cookies from JS
SESSION_COOKIE_HTTPONLY = False
```

Add to the end:
```
DISCORD_CLIENT_ID = [Place_Client_ID_Here]
DISCORD_CLIENT_SECRET = "[Place_Client_Secret_Here]"
DISCORD_REDIRECT_URI = "http://example.test:5000/auth/discord-callback" #Site need to be equal SERVER_NAME
DISCORD_BOT_TOKEN = "[Place_Bot_Token_Here]"
DEBUG_TB_INTERCEPT_REDIRECTS = False
```

* Make your discord bot and replace placeholders in `flaskbb.cfg` which we added earlier
	[Developers Applications](https://discord.com/developers/applications)
	[Guide to them](https://discordpy.readthedocs.io/en/stable/discord.html)
	Add redirect to your DISCORD_REDIRECT_URI

* Enable OAUTHLIB_INSECURE_TRANSPORT
`export OAUTHLIB_INSECURE_TRANSPORT=1`

* Compile themes
```
cd ./flaskbb/themes/onyx && npm run build:all
cd ../aurora && npm run build:all
```

### Starting this monster:
```
make install #Need to be written once
make run
```

Ignore any errors at `make install` it's executing once time

* Go to your `SERVER_NAME` and log in
* Change your `primary_group_id` in `flaskbb.sqlite -> users` to `1`
* Refresh page. Congrats you're now Admin
* Go to `http://example.test:5000/admin/ -> Settings -> Appearance Settings -> Default Theme = Onyx -> Save`
* Go to `http://example.test:5000/admin/ -> Plugins -> Portal -> Disable`

# DB setup
* Add `ruble` to `onyx -> money_currencies`
* Add `donation` to `onyx -> point_transaction_types`
* Add `other` to `onyx -> point_transaction_types`
* Add `any` to `onyx -> donations_types`
* Add `discord_id` and your `discord_nickname` to `onyx -> dicord_users`
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

* `touch modules/hub/hub/servers_config.py`
* Write this:
```
import attr
from typing import List, Dict


@attr.s(auto_attribs=True)
class ServerDescriptor:
    id: str
    name: str
    service_name: str
    path: str
    branch_name: str
    dream_maker_binary: str
    dme_name: str
    base_permission: str
    additional_permission: str
    management_permission: str
    discord_full_access_titles: List[str]
    discord_base_access_titles: List[str]
    discord_role_to_group: Dict[str, int]
    configs_path: str
    configs_exclude: List[str]
    logs_path: str

servers_config = [
    ServerDescriptor(
        id="chaotic",
        name="Chaotic Onyx",
        service_name="onyx.service",
        path="~/OnyxBay/",
        branch_name="release/chaotic",
        dream_maker_binary="DreamMaker",
        dme_name="baystation12.dme",
        base_permission="onyx_base",
        additional_permission="onyx_additional",
        management_permission="onyx_management",
        discord_full_access_titles=[

        ],
        discord_base_access_titles=[

        ],
        discord_role_to_group = {

        },
        configs_path="~/OnyxBay/config/",
        configs_exclude=["dbconfig.txt", "dbconfig_docker.txt"],
        logs_path="~/OnyxBay/data/logs")
]
```

# Misc

* For hub log
**Don't forget change <server_id>**
```
mkdir logs/<serverd_id>
touch logs/<serverd_id>/update.log
touch logs/<serverd_id>/server.log
```