#!/bin/sh

gcc main.c -o main \
  -O0 -fno-omit-frame-pointer -fstack-protector-all \
  -no-pie -z noexecstack -D_FORTIFY_SOURCE=0 \
  -lcrypto
