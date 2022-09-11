#!/bin/bash

ln -s $(pwd)/gpufan /usr/bin/gpufan
cp gpufan.service /etc/systemd/system/gpufan.service
systemctl daemon-reload
systemctl enable --now gpufan
