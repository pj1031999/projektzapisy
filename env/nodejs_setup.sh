#!/usr/bin/env bash

# Install nodejs
curl -sL https://deb.nodesource.com/setup_10.x | bash -
apt-get install -y nodejs

# Install yarn, needed globally
npm i -g yarn
