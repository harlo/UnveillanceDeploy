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

		echo "Restarting container..."
		sudo docker start unveillance_stub

		echo "Committing container..."
		sudo docker commit unveillance_stub ${BUILD_DATA[1]}

		echo "Building ${BUILD_DATA[1]} to run..."
		sudo docker build -t ${BUILD_DATA[1]} .

		rm commit_image.txt
		rm Dockerfile
		echo "FINISHED!"
	fi
fi