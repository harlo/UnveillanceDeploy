#! /bin/bash

python build_image.py $1 $2
BUILD_IMAGE=$?

if ([ $BUILD_IMAGE -eq 0 ])
then
	IFS=$'\n' read -d '' -r -a BUILD_DATA < $1/lib/commit_image.txt
	for c in "${BUILD_DATA[@]}"
	do
		echo $c
		$c
	done

	echo "FINISHED!"
fi