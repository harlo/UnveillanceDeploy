#! /bin/bash

python image.py
BUILD_IMAGE=$?

if ([ $BUILD_IMAGE -eq 0 ])
then
	if [[ $(find commit_image.txt) == "commit_image.txt" ]]
	then
		IFS=$'\n' read -d '' -r -a BUILD_DATA < commit_image.txt
		echo "NOW RUNNING ANNEX SETUP ON ${BUILD_DATA[1]}"

		${BUILD_DATA[0]}
		sudo docker start unveillance_stub
		sudo docker commit unveillance_stub ${BUILD_DATA[1]}
		sudo docker build -t ${BUILD_DATA[1]} .

		rm commit_image.txt
		rm Dockerfile
	fi
fi