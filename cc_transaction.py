"""
Author: M I Schwartz

This class encapsulates the creation and most common manipulations of a
    Credit Card transaction object.
It is primarily based on Stripe.com and Authorize.net models,
    but simplified for use in a classroom exercise

In particular, utility functions are provided:
    * to validate a transaction by checking format, length, vendor, and cvv length
    * to convert the transaction object to JSON
    * to convert JSON to a transaction object
    * to construct a transaction from user information
    * to set the merchant data into the transaction properly
        (done by merchant site before authorization)

The functions also take parameters and return useful information to debugging problems.
"""

import json
import uuid
import logging
import validation_utilities


class CCTransaction:
    """A simplified Credit Card transaction"""

    enableAuthorizationChecks = False # By default, disable

    def __init__(self, name="", credit_card_string="", cvv_string="", exp_month=0,
                 exp_year=2000, currency="usd"):
        """Initialize a transaction object"""
        self.data = {}
        self.data["card"] = {"id": credit_card_string, "name": name,
                             "card_code": cvv_string, "currency": currency,
                             "exp_month": exp_month, "exp_year": exp_year}
        self.data["id"] = "auth_" + str(uuid.uuid4())
        self.data["currency"] = currency
        self.data["amount"] = 0

    def set_authorization_checks(value=True):
        CCTransaction.enableAuthorizationChecks = value

    def set_amount(self, amount, currency="usd"):
        """sets the amount of the transaction in cents"""
        self.data["amount"] = int(amount)
        self.data["currency"] = currency
        return self

    def set_amount_dc(self, dollars, cents=0, currency="usd"):
        """sets the amount of the transaction in dollars and cents"""
        self.data["amount"] = dollars * 100 + cents
        self.data["currency"] = currency
        return self

    def get_amount(self):
        """returns the amount from the transaction object"""
        return self.data["amount"]

    def get_name(self):
        """returns the cardholder's name fro the transaction object"""
        return self.data["card"]["name"]

    def set_merchant_data(self, merchant_name, merchant_id):
        """sets the merchant data properly into the transaction object"""
        self.data["merchant_data"] = {"name": merchant_name, "network_id": merchant_id}

    def is_ready_for_request(self):
        """Checks for basic data, not its validity"""
        has_cardholder_info = "id" in self.data and "card" in self.data
        has_card_info = False
        if has_cardholder_info:
            card_info = self.data["card"]
            has_card_info = ("id" in card_info) and \
                            ("name" in card_info) and ("currency" in card_info) and \
                            ("exp_month" in card_info) and \
                            ("exp_year" in card_info) and ("card_code" in card_info)

        has_merchant_info = "merchant_data" in self.data and "name" in self.data["merchant_data"] \
                            and "network_id" in self.data["merchant_data"]

        return has_cardholder_info and has_card_info and has_merchant_info and \
               self.data["amount"] > 0

    def to_json(self):
        """Returns the transaction object as a JSON string"""
        return json.dumps(self.data)

    @classmethod
    def list_to_json(cls, list_of_transactions):
        """Converts a list of transactions into a JSON string"""
        intermediate = []
        for transaction in list_of_transactions:
            intermediate.append(transaction.data)
        return json.dumps(intermediate)

    @classmethod
    def json_to_list(cls, json_string):
        """Converts a json string into a list of transactions"""
        intermediate = json.loads(json_string)
        if isinstance(intermediate, list):
            for i in range(0, len(intermediate)):
                intermediate[i] = cls.from_dict(intermediate[i])
        elif isinstance(intermediate, str):
            logging.debug("  DEBUG: intermediate: %s\n",intermediate)
        else:
            logging.debug("  DEBUG: type: %s\n",str(type(intermediate)))
        return intermediate

    @classmethod
    def from_json(cls, json_string):
        """Sets the transaction data to the contents of the JSON"""
        result = cls()
        result.data = json.loads(json_string)
        return result

    @classmethod
    def from_dict(cls, transaction_dict):
        """Sets the transaction data from the contents of a dict"""
        result = cls()
        for key in transaction_dict.keys():
            if key in ("card", "merchant_data"):
                if isinstance(transaction_dict[key], dict):
                    for k in transaction_dict[key].keys():
                        if not key in result.data:
                            result.data[key] = {}
                        result.data[key][k] = transaction_dict[key][k]
                else:
                    logging.debug("Warning: dictionary "+key+" not overwritten.\n")
            else:
                result.data[key] = transaction_dict[key]
        return result

    def update_from_json(self, json_string):
        """Updates self from response to a web service"""
        cc_response = CCTransaction.from_json(json_string)
        logging.info("Response: %s\n",cc_response.to_json())

        # Do any validation needed to ensure the response is ok
        ok = True
        for key in self.data:
            if not key in cc_response.data:
                logging.warning("Response is missing %s\n",key)
                ok = False
        for key in self.data["card"]:
            if not key in cc_response.data["card"]:
                logging.warning("Response is missing card: %s\n",key)
                ok = False
        # End of validation

        if ok:
            return cc_response

        logging.error("Response does not match query. Skipping response.\n")
        return self

    def validate_card(self):
        """Validate a card's number is sensible and store its vendor"""
        card_data = self.data["card"]
        result = validation_utilities.validate_card(card_data["id"], card_data["card_code"], True)
        self.data["card"]["valid"] = result[0]
        if len(result) > 1:
            self.data["card"]["type"] = result[1]
        return result[0]

    def validate_date(self):
        """Validate the expiration date"""
        if "exp_month" in self.data["card"] and "exp_year" in self.data["card"]:
            return validation_utilities.validate_date(self.data["card"]["exp_month"],
                                                      self.data["card"]["exp_year"])
        logging.error("Can't find expiration data.\n")
        return True

    def validate_transaction(self):
        """
        Validate a transaction
        This checks the card as provided to card format and vendor are sensible,
        that merchant information is provided,
        that the transaction amount is below a fixed limit,
        and that the expiration date provided is sensible.
        """
        status = True
        if not self.validate_card():
            self.data["approved"] = False
            self.data["failure_code"] = 401
            self.data["failure_message"] = "Card is not valid"
            status = False
        elif not self.is_ready_for_request():
            self.data["approved"] = False
            self.data["failure_code"] = 402
            self.data["failure_message"] = "Missing information for transaction approval"
            status = False
        elif int(self.data["amount"]) < 0 or int(self.data["amount"]) > 500000:
            self.data["approved"] = False
            self.data["failure_code"] = 405
            self.data["failure_message"] = "Transaction amount threshold exceeded"
            status = False
        elif not self.validate_date():
            self.data["approved"] = False
            self.data["failure_code"] = 408
            self.data["failure_message"] = "Invalid expiration date"
            status = False
        else:
            self.data["approved"] = True
            self.data["failure_code"] = ''
            self.data["failure_message"] = ''
            # self.data["approval_code"] = "tmpappr_" + str(uuid.uuid4())
        return status

    def authorize_transaction(self):
        """
        A true credit card processor would verify the card has been issued,
        the information matches the card
        It would also verify the merchant is legitimate and the information matches the merchant.
        Other checks might also occur to prevent fraud.
        """
        from ccstore import cc_enrolled, cc_get_customer_id, cc_check_code, cc_get_limit
        status = True
        # Shortcut out if individual accounts are not enabled.
        if not CCTransaction.enableAuthorizationChecks:
            self.data["authorized"] = True
            self.data["approval_code"] = "appr_" + str(uuid.uuid4())
            return status
        card_id = self.data["card"]["id"]
        if cc_enrolled(card_id):
            customer_id = cc_get_customer_id(card_id)
            if (cc_check_code(customer_id,self.data["card"]["card_code"])):
                limit = cc_get_limit(customer_id)
                if int(self.data["amount"] < int(limit)):
                    self.data["authorized"] = True
                    self.data["approval_code"] = "appr_" + str(uuid.uuid4())
                else:
                    self.data["authorized"] = False
                    self.data["failure_code"] = 405
                    self.data["failure_message"] = "Account threshold exceeded"
                    status = False
            else:
                self.data["authorized"] = False
                self.data["failure_code"] = 411
                self.data["failure_message"] = "Card code incorrect"
                status = False
        else:
            self.data["authorized"] = False
            self.data["failure_code"] = 401
            self.data["failure_message"] = "Credit card account not found"
            status = False
        return status
