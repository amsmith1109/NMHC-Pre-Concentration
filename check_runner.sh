a=$(ps -ef|grep python|grep pre_con|awk '{print $2}')
echo $a