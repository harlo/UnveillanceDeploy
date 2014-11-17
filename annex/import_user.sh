#! /bin/bash

CMD=$(echo $(sudo docker inspect $1) | python -c 'from container import import_user;import_user("'$2'","'$3'");')
echo $CMD