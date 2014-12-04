#! /bin/bash

CMD=$(echo $(sudo docker inspect $1) | python -c 'from container import get_config;get_config("'$2'",as_local='$3')')

echo "*** CONFIG SAVED TO configs/$CMD.json ***"
echo ""
cat configs/$CMD.json
echo ""
echo "****"