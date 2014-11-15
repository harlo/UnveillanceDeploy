#! /bin/bash

python image.py
BUILD_IMAGE=$?

if ([ $BUILD_IMAGE -eq 0 ])
then
	IFS=$'\n' read -d '' -r -a BUILD_DATA < lib/commit_image.txt
	for c in "${BUILD_DATA[@]}"
	do
		echo $c
		$c
	done

	echo "FINISHED!"
fi