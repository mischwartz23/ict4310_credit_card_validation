#!/bin/sh
# Author: M I Schwartz
# This script settles any remaining transactions in the credit_card_processing_service
echo Settling outstanding Credit Card Network transactions

# Set these to match your desired port and protocol
PORT=8000
PROTOCOL=http

URL_STORE="${PROTOCOL}://localhost:${PORT}/api/store"
URL_SETTLE="${PROTOCOL}://localhost:${PORT}/api/settle"

verbose='{"verbose":true}'

data=`curl -d "${verbose}" ${URL_STORE}`

echo Initial unsettled transactions: "${data}"

result=`curl -d "${data}" ${URL_SETTLE}`

newdata=`curl -d "${verbose}" ${URL_STORE}`

echo Final unsettled transactions: "${newdata}"

