@echo off
chcp 65001

nuitka ^
  --mingw64 ^
  --lto=yes ^
  --standalone ^
  --assume-yes-for-downloads ^
  --enable-plugin=tk-inter ^
  --windows-disable-console ^
  --output-dir=dist ^
  --remove-output ^
  --show-progress ^
  --include-data-file=creazymouse.ico=creazymouse.ico ^
  --windows-icon-from-ico=creazymouse.ico ^
  --windows-uac-admin ^
  --output-filename=疯狂的老鼠 ^
  creazymouse.py