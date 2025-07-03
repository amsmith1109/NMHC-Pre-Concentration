pid=$(bash check_runner.sh)
#if [-z "$pid"] then
#    echo "Pre-concentration system is currently running."
#    read -p "kill process and continue? (y/n):" confirm && $confirm==[yY] || #kill -9 $pid
#fi
dt=$(date '+%I-%M %p on %h %d, %Y')
dt=$(date '+[%Y] %h %d, %I-%M %p')
out_dir="logs/Sequence logs/$dt.txt"
touch "$out_dir"
echo Logging output to: $out_dir
nohup python -u pre_con.py -s 'DR.txt' --continuous > "$out_dir" &
exec $SHELL
