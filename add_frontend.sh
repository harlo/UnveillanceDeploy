#! /bin/bash
THIS_DIR=`pwd`

cd annex
CMD=$(echo $(sudo docker inspect $1) | python -c 'from container import get_config;get_config("'$2'",as_local=False)')

echo "*** CONFIG SAVED TO configs/$CMD.json ***"
echo ""
cat configs/$CMD.json
echo ""
echo "****"

cd $THIS_DIR
./build_image frontend annex/configs/$CMD.json