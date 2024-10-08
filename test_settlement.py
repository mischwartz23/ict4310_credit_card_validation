"""
   Author: M I Schwartz
   Tests a settlement
"""
from cc_transaction import *
from cc_settlement import *

import json

import requests

url = "http://localhost:8000/api/validate"
url_ssl = "https://localhost:8443/api/validate"
surl = "http://localhost:8000/api/settle"
surl_ssl = "https://localhost:8443/api/settle"

# Create a transaction
my_transaction = CCTransaction("ICT4310 Instructor", "4140-1233-3445-4561",
                               "123", "12", "2028", "usd")
# Set the amount
my_transaction.set_amount(10000)  # $100.00
# Add the merchant information
my_transaction.set_merchant_data("Target", "merch_1e_2f_3g")

# Validate the transaction
try:
    validated_transaction = requests.post(url, data=my_transaction.to_json())
except:
    print("Cannot connect to validate service")
    exit()

cc_transaction = my_transaction.update_from_json(validated_transaction.text)
cc_transaction.data["approval_code"] = "73" # <- invalid
# Create a settlement batch
batch_json = CCTransaction.list_to_json([ cc_transaction ])
try:
    settled = requests.post(surl, data=batch_json)
except:
    print("Cannot connect to settle service")
    exit()

print (CCSettlement.from_json(settled.text).to_json())
