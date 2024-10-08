""" post client example """
# Author: Michael Schwartz
# File:   testTransaction.py
# Based on post.py by Robb Judd
# Relies on supporting both HTTP and HTTPS on ports 8000 and 8443 respectively.
# Modify or comment out if your service does not support these
# This example is intended to test the POST path.
# Additional tests could be created to test various error conditions as well.

import requests

from cc_transaction import CCTransaction

url = "http://localhost:8000/api/validate"
# Create a transaction
my_transaction = CCTransaction("ICT4310 Instructor", "4140-1233-3445-4561",
                               "123", "12", "2028", "usd")
# Set the amount
my_transaction.set_amount(10000)  # $100.00
# Add the merchant information
my_transaction.set_merchant_data("Target", "merch_1e_2f_3g")

print("\n** HTTP: Expect success **\n")
response = requests.post(url, data=my_transaction.to_json())
print(response.text)

my_bad_transactions = [ CCTransaction("ICT4310 Instructor", "4140-1233-3445-4560",
                                      "123","12","2028", "usd"),
                        CCTransaction("ICT4310 Instructor", "4140-1233-3445-4561",
                                      "1234","12","2028", "usd"),
                        CCTransaction("ICT4310 Instructor", "4140-1233-3445-4561",
                                      "123","03","2022", "usd")
                      ]

for transaction in my_bad_transactions:
    transaction.set_amount("10000")
    transaction.set_merchant_data("Target", "merch_1e_2f_3g")
    print("\nBad Transaction\n")
    response = requests.post(url, data=transaction.to_json())
    print(response.text)

# settle
print("Settle");
response = requests.post("http://localhost:8000/api/settle", {"data": "empty"});
print(response.text);

# store
print("Store");
response = requests.post("http://localhost:8000/api/store", {"data": "empty"});
print(response.text);

# nonesuch
print("Bad path");
response = requests.post("http://localhost:8000/nonesuch", {"data": "empty"} );
print(response.text);

# GET requests
print("GET");
response = requests.post("http://localhost:8000/nonesuch");
print(response.text);

print("Done")
