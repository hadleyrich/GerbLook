GerbLook
=======
Copyright 2013 Hadley Rich, nice technology Ltd.  and contributors

Website: <http://nice.net.nz>

A web based gerber renderer based on Python, gerbv and imagemagick held together with a little glue and string.

Running your own instance
-------------------------
The following setup is tested under Ubuntu Linux, if you are using another system like MacOS or another Linux distribution you may have to adjust the commands to install the software.

#### Installing the required software on Linux
1) Install Redis: `sudo apt-get install redis-server`
2) Install libpq-dev, imagemagick and gerbv: `sudo apt-get install libpq-dev imagemagick gerbv`
3) Install Python PIP: `sudo apt install python-pip`
4) Install Git: `sudo apt install git`

#### Downloading and installing GerbLook
1) Clone the GerbLook Sourcecode: `git clone https://github.com/hadleyrich/GerbLook.git`
2) Change into the GerbLook folder: `cd GerbLook`
3) Install PIP requirements: `pip install -r requirements.txt`

#### Starting GerbLook
1) Run the renderer: `./renderer.py &`
2) Run the manager:`./manage.py`
3) Open your browser at:  `127.0.0.1:5000`
4) Enjoy using GerbLook

LICENSE
-------
BSD - See LICENSE file

