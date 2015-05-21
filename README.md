GerbLook
=======
Copyright 2013 Hadley Rich, nice technology Ltd.  
Website: <http://nice.net.nz>

A web based gerber renderer based on Python, gerbv and imagemagick held together with a little glue and string.

Running your own instance
-------------------------

- Install [Redis](http://redis.io/) and run redis-server (default port is 6379 which will work)
- Install `libpq-dev`,`imagemagick` and `gerbv`
- `pip install -r requirements.txt`
- `./renderer.py &`
- `./manage.py` and direct your browser to `0.0.0.0:5000`

LICENSE
-------
BSD - See LICENSE file
