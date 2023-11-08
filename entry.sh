#!/bin/sh

printf "\033[0;32mStarting Container...\033[0m\n"

# Update pip and install required package
printf "\033[0;32mUpgrading pip...\033[0m\n"
pip install --upgrade pip
printf "\033[0;32mInstalling dependencies...\033[0m\n"
pip install orjson
printf "\033[0;32mDone...\033[0m\n"

printf "\033[0;32mConverting all movies to mkv\033[0m\n"
python3 m2ts_to_mkv.py || printf "\033[0;32mPython script failed with exit code $?\033[0m\n"
printf "\033[0;32mConverting finished...\033[0m\n"
printf "\033[0;32mContinuing to remove languages\033[0m\n"

printf "\033[0;32mRemoving languages\033[0m\n"
python3 Remove_Languages.py || printf "\033[0;32mPython script failed with exit code $?\033[0m\n"

printf "\033[0;32mScript have finished, container is exiting\033[0m\n"
