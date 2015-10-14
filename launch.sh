#!/bin/sh
cd /
cd ~/BitFarm.io
python control.py >> /tmp/control.log&
python gateway.py >> /tmp/gateway.log&
python db.py >> /tmp/db.log&
python notify.py >> /tmp/notify.log&
python snapshot.py --port 8080 --conf ~/BitFarm.io/config/snapshot.local.txt --freq 3600 --dir ~/BitFarm.io/pics >> /tmp/snapshot.log&
