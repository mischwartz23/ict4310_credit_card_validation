"""
Author: M I Schwartz

This class encapsulates the creation and most common manipulations of a
    Credit Card settlement object.

It is primarily based on Stripe.com and Authorize.net models,
    but simplified for use in a classroom exercise

In particular, utility functions are provided:
    * to check that a Credit Card transaction has been authorized
    * to convert the settlement object to JSON
    * to convert JSON to a settlement object
    * to convert a dict into a settlement object
    * to create a settlement uuid and add it to the transaction

The functions also take parameters and return useful information to debugging problems.

Use case outline:
    Merchant creates a settlement batch: an array of my_bad_transactions
    These transactions should have been authorized previously
    Credit card processor returns a settlement object
        Has a unique settlement id
        Each approved transaction is marked with the settlement id
        Structure is: {   settlement_id: uuid,
                          transactions: [ included transactions ],
                          unsettled: [ not included transactions ]
                      }
        Transactions are structured via cc_transaction, except they also have a
        "settled" attribute whose value is the same as that in the global settlement id

"""
import json
import uuid
import datastore

from cc_transaction import CCTransaction

# MAX_SETTLEMENTS = 100

class CCSettlement:
    """
    A settlement object is a batch of transactions together with a settlement id
    A settlement may not contain zero transactions

    """

    def __init__(self):
        self.settlement_id = "pending"
        self.transactions = []
        self.unsettled = []

    @classmethod
    def check_transaction(cls, transaction, g_list, c_list, m_list):
        """Check the transaction for proper fields and completeness"""
        result = True
        message = []
        # Check card attributes
        for attr in c_list:
            if not attr in transaction.data["card"]:
                message.append(attr + " not found in card data")
                result = False
        # Check merchant attributes
        for attr in m_list:
            if not attr in transaction.data["merchant_data"]:
                message.append(attr + " not found in merchant data")
                result = False
        # Check for validity and authorization
        for attr in g_list:
            if not attr in transaction.data:
                message.append(attr + " not found in transaction data")
                result = False
        if len(message) > 0:
            print("Transaction "+
                  transaction.data.to_json()+
                  " not accepted: "+", ".join(message))
        return result

    @classmethod
    def settle(cls, transactions):
        """
            Checks a single transaction and adds a settlement id if OK
            This should use the persistent store to verify settlements,
            log the completed ones, and remove the transactions from the
            pending list.
        """
        result = cls()
        for transaction in transactions:
            print(transaction)
            if CCSettlement.check_transaction(transaction=transaction,
                                              g_list=["approved", "approval_code"],
                                              c_list=["type", "valid"],
                                              m_list=["name", "network_id"]):
                # Check if the card IS valid and IS authorized
                if "approved" in transaction.data and transaction.data["approved"] \
                   and "approval_code" in transaction.data and transaction.data["approval_code"]:
                    if result.settlement_id == "pending":
                        result.settlement_id = "settle_" + str(uuid.uuid4())
                    transaction.data["settlement_id"] = result.settlement_id
                    result.transactions.append(transaction)
                    datastore.settle(transaction.data["approval_code"])
                else: # Did not pass the test
                    result.unsettled.append(transaction)
            else:
                result.unsettled.append(transaction)
        return result

    def to_json(self):
        """Returns the settlement object as a JSON string"""
        result = {
            "settlement_id": self.settlement_id,
            "transactions":  self.transactions,
            "unsettled":     self.unsettled
        }
        result["transactions"] = []
        for t in self.transactions:
            result["transactions"].append(t.data)
        result["unsettled"] = []
        for u in self.unsettled:
            result["unsettled"].append(u.data)
        return json.dumps(result)

    @classmethod
    def from_json(cls, json_string):
        """Create CCSettlement from a JSON string"""
        result = cls()
        expand = json.loads(json_string)
        result.settlement_id = expand["settlement_id"]
        transactions = expand["transactions"]
        for trans in transactions:
            transaction = CCTransaction.from_dict(trans)
            if not "settlement_id" in transaction.data:
                result = result.settle([transaction])
            elif transaction.data["settlement_id"] == result.settlement_id:
                result.transactions.append(transaction)
            else: # Problem! already settled by a different batch number
                print("   Transaction already settled with a different batch")
        return result

    @classmethod
    def from_dict(cls, transaction_dict):
        """Create CCSettlement from a dict"""
        result = cls()
        if "settlement_id" in transaction_dict and "transactions" in transaction_dict:
            result.settlement_id = transaction_dict.settlement_id
            for transaction in transaction_dict.transactions:
                if not transaction["settlement_id"]:
                    result = result.settle(transaction)
                elif transaction.settle == result.settlement_id:
                    result.transactions.append(transaction)
                else: # Problem! already settled by a different batch number
                    print("   Transaction already settled with a different batch")
            for transaction in transaction_dict.unsettled:
                result.unsettled.append(transaction)
        return result
