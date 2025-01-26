% Author: Michael Schwartz
% Title: README for credit_card_validation_services

Introduction
------------

This document contains a summary of the credit_card_validation_services API

The basic structures for interchange are described.

All input data and output data are JSON.

Routes
-------------------

- /hello
  - A "ping" route to check if the server is running.
  - This is a GET route; all APIs are POST routes
- /api/validate
  - Used to validate credit cards (Luhn, vendor, expiration, merchant, and amount)
  - Input is a card info structure
  - Output is a validation structure
  - Validated transactions are saved to match to a settlement request
- /api/settle
  - Used to settle a Transaction
  - Input is an list (array) of validated Transactions
  - Output is a settlement structure
  - Settled transactions are unsaved
- /api/store
  - Used to retrieve transactions that have not been settled
    - Primarily a debug tool
  - Input is a record with a "verbose" key set to true or false
  - Output is an array of authorization ids or authorizations that have not been settled

Card info structure
-------------------

In the _real world_, a valid card info structure is replaced with a token as early as possible.

```
{
    "card_code": 3-or-4-digit string,
    "currency": ISO-currency-abbrev,
    "exp_month": 2-digit-string,
    "exp_year": 4-digit-string,
    "id": credit-card-number-string,
    "name": cardholder-name-string,
    "type": card-vendor-string, // Filled on validate
    "valid": true_or_false    // Filled on validate
}
```
Transaction structure
---------------------

```
{
  "amount": number-in-lowest-denominated-currency,
  "approval_code": "appr_"+uuid, // Filled if authorized
  "approved": true_or_false,     // Filled on validate
  "authorized": true_or_false,   // Filled on authorize
  "card": Card-Info-Structure,   // See above. Updated on validate
  "currency": ISO-currency-abbrev,
  "failure_code": string,        // Filled on validate. Empty string if approved
  "failure_message": string,     // Filled on validate. Empty string if approved
  "id": "auth_"+uuid,            // Transaction id created by merchant
  "merchant_data": {             // Added by merchant
    "name": merchant-name,
    "network_id": merchant-id-code
  },
  "settlement-id": "settle_"+uuid // Added by settlement
}
```

The file `OK_transaction.json` contains a filled-out and valid transaction structure

Settlement structure
--------------------

Settlement adds the settlement_id to each settled transaction, as well.

```
{
  "settlement_id": "settle_"+uuid,   // Added by settlement
  "transactions": [ Transaction-Structure, ... ],
  "unsettled": [ Transaction-Structure, ... ]
}
```
Store input structure
---------------------

If verbose is true, the response will include the Transaction detail; if not, just the Transaction approval codes.
```
{ "verbose": true_or_false }
```

Store response structure
------------------------

If verbose is set to false:

```
[ transaction-approval-code-string, ... ]
```

If verbose is set to true:

```
[ Transaction-Structure, ... ]
```
Scripts
------------------

The root and the test directory contain scripts and tests.
A brief description follows

| File             | Purpose                                         | Invocation                  |
|------------------|-------------------------------------------------|-----------------------------|
| MANIFEST.in      | Not used at this time                           | -                           |
| README.md        | This file                                       | -                           |
| requirements.txt | Contains python packages to be installed by pip | _build process consults it_ |
| tests            | Contains tests scripts and support              | -                           |
| \_\_init\_\_.py  | Allows scripts to be imported from the REPL     | -                           |

Sources
-----------------------

| File                              | Purpose                                    |
|-----------------------------------|--------------------------------------------|
| cc_settlement.py                  | settlement class                           |
| cc_transaction.py                 | transaction class                          |
| credit_card_validation_service.py | web server with services                   |
| datastore.py                      | in-memory store for unsettled transactions |
| validation_utilities.py           | Support functions                          |

\* Not included in the zip file.

Setting up the example to run
-----------------------------

The credit card network server is `credit_card_validation_service.py`. 
It runs unencrypted on port 8000, and encrypted on port 8443.
To use https, you must create a `.pem` file with your key and certificate. 
Directions are in `credit_card_validation_service.py`
Start it in a command prompt window with `python3 credit_card_validation_service.py`

The other files mentioned are imported by the servers.

The credit_card_validation_service is "primed" with the data in `enrolled_credit_cards.json`. This file can be edited with a text editor. It is a JSON file.

The other python scripts require the _requests_ module, so please set up a virtual environment to run these

Tests
-----------------------

The remainder of the files are for testing.
These are the tests.

The Python scripts all require version 3 of Python.

| File                   | Purpose                                                          | Invocation                   |
|------------------------|------------------------------------------------------------------|------------------------------|
| create_pem.sh          | Uses openssl to create a key and certificate                     | sh create_pem.sh             |
| test_ccnv_form.html    | Form to test the credit card processor API                       | Open page in web browser     |
| settle_remaining.sh    | Uses curl to settle all outstanding transactions in one batch    | sh settle_remaining.sh       |
| test_store_status.html | Web page to invoke /api/store and display unsettled transactions | open page in web browser     |
| test_settlement.py     | Create a transaction and settle it                               | python  test_settlement.py   |
| test_settlement10.py   | Create 10 transactions and settle them                           | python test_settlement10.py  |
| test_transaction.py    | Create several transactions, some good and some bad              | python test_transaction.py   |
