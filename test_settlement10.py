"""
   Author: M I Schwartz
   Tests a batch of settlements
"""
from cc_transaction import *
from cc_settlement import *

import json

import requests

url = "http://localhost:8000/api/validate"
surl = "http://localhost:8000/api/settle"

# Create an array of transactions
my_transactions = []
for i in range(0,10):
    my_transaction = CCTransaction("ICT4310 Instructor", "4140-1233-3445-4561",
                               "123", "12", "2028", "usd")
    # Set the amount
    my_transaction.set_amount(10000 + i * 105 )  # $100.00
    # Add the merchant information
    my_transaction.set_merchant_data("Target", "merch_1e_2f_3g")
    # Validate the transaction
    try:
        validated_transaction = requests.post(url, data=my_transaction.to_json())
    except:
        print("Cannot connect to validate service")
        exit()
    cc_transaction = my_transaction.update_from_json(validated_transaction.text)
    # cc_transaction.data["approval_code"] = "73" # <- invalid
    my_transactions.append(cc_transaction)

# Create a settlement batch
batch_json = CCTransaction.list_to_json(my_transactions)
try:
    settled = requests.post(surl, data=batch_json)
except:
    print("Cannot connect to settle service")
    exit()

settlement = CCSettlement.from_json(settled.text)
# settlement = settled.json()

print ("There are "+str(len(settlement.transactions))+" settled transactions and "+
       str(len(settlement.unsettled))+" unsettled transactions")
