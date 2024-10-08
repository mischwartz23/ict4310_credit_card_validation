#!/bin/sh
# Author: M I Schwartz
# Last updated: 2024-10-06
# Note: User must fill out the prompts
# Note: Keep the resulting files private, even though they are temporary.

openssl req -new -x509 -keyout localhost.pem -newkey rsa:2048 -out localhost.pem -days 365 -nodes
