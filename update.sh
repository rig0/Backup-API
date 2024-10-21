#!/bin/bash
git clone git@ssh.rigslab.com:Rambo/Backup-API.git temp
cp -R temp/* .
rm -R -f temp