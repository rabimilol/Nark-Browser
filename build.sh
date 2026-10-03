#!/bin/bash
set -e

apt-get update
apt-get install -y \
    python3-pip \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-webkit2-4.1 \
    binutils

pip3 install pyinstaller

pyinstaller --onefile --hidden-import=gi --name=Nark-Browser src/main.py
