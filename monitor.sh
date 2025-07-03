cd /home/pi/NMHC-Pre-Concentration/
pid=$(bash check_runner.sh)
cd "/home/pi/NMHC-Pre-Concentration/logs/Sequence logs/"
recent=$(ls -t|head -1)
tail -f "$recent" --pid $pid
