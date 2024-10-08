"""
   Author: M I Schwartz

   Stores / retrieves a single "dict"
   The intent is that this file stores all the enrolled credit cards
   for the mock service.
"""

import json

from validation_utilities import validate_card, validate_date

_CCSTORE = { }

# Need: Read file to load _CCSTORE
# Need: Checker to get card info matching card

_CC_FILE_NAME = "enrolled_credit_cards.json"

def _init_ccstore(filename):
    try:
        f = open(filename,)
        data = json.load(f)
        f.close()
        _validate_cc_data(data)
    except json.JSONDecodeError as err:
        print("\n\n*** Cannot parse " + filename + ": {0}\n\n".format(err))
    except FileNotFoundError as err:
        print("\n\n*** Cannot open file {0}\n\n".format(err))


def cc_enrolled(cc_id):
    return cc_id in _CCSTORE

def cc_get_customer_id (cc_id):
    if cc_enrolled(cc_id):
        rec = _CCSTORE[cc_id]
        return rec["customer_id"]

def cc_check_code(customer_id, code):
    rec = _CCSTORE[customer_id]
    return rec["card_code"] == code

def cc_get_limit(customer_id):
    rec = _CCSTORE[customer_id]
    return rec["card_limit"]

def _validate_cc_data(data):
    count = 0
    for card in data:
        count = count + 1
        print("Reading card " + str(count))
        cardRecord = { }
        valid = True
        for field in { "authorizing_bank", "card_code", "card_limit", "currency",
                       "exp_month", "exp_year", "id", "name", "zip_code"}:
            if not field in card or not card[field]:
                print ( card["id"] + " is not valid. Missing field " + field )
                valid = False
            else:
                cardRecord[field] = str(card[field]).strip()
        if valid:
            # Validate the CC id
            if validate_card(card["id"], card["card_code"]):
                if validate_date(card["exp_month"], card["exp_year"]):
                    _CCSTORE[card["id"]] = card
                    _CCSTORE[card["customer_id"]] = card
                else:
                    print ( card["id"] + " is not valid. Expiry date is not accepted.")
            else:
                print( card["id"] + " is not valid. Card id malformed.")

_init_ccstore(_CC_FILE_NAME)
