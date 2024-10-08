"""
    Author: M I Schwartz

    This is a collection of functions and data to validate credit card numbers

    * A credit card dictionary object with regular expressions to match vendor credit card formats
    * credit_card_vendor checks a credit card number's format and returns the vendor,
         if it is a valid card number
    * validate_card checks the credit card format and cvv
    * verify_luhn is a credit card format check to ensure the last digit of the
        credit card is correct
    * validate_cvv checks the cvv against the credit card to ensure it is of the proper length
    * validate_date checks the expiration month and year against the current date.
        Expiration must be within 5 years.
"""

import re
import datetime

cc_dictionary = {
    'visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
    'mastercard': r'^5[1-5][0-9]{14}$|^2(?:2(?:2[1-9]|[3-9][0-9])|[3-6][0-9][0-9]|7(?:[01][0-9]|20))[0-9]{12}$',
    'amex': r'^3[47][0-9]{13}$',
    'discover': r'^65[4-9][0-9]{13}|64[4-9][0-9]{13}|6011[0-9]{12}|(622(?:12[6-9]|1[3-9][0-9]|[2-8][0-9][0-9]|9[01][0-9]|92[0-5])[0-9]{10})$',
    'diners_club': r'^3(?:0[0-5]|[68][0-9])[0-9]{11}$',
    'jcb': r'^(?:2131|1800|35[0-9]{3})[0-9]{11}$'
}

def credit_card_vendor(credit_card_string):
    """ Returns credit card vendor info, or False if card is invalid """
    credit_card = re.sub(r'[\D]', '', credit_card_string)
    for key, value in cc_dictionary.items():
        if re.fullmatch(value, credit_card):
            return key
    return False

def validate_card(credit_card, cvv, result_list=False):
    """
    Returns False if card or cvv are invalid length or formnat;
    returns True or components for test if result_list=True
    """
    card_type = credit_card_vendor(credit_card)
    valid = verify_luhn(credit_card)
    cvv = validate_cvv(credit_card, cvv)
    print("Type: ", card_type, " Luhn: ", valid, " cvv", cvv)
    if result_list:
        return (card_type and valid and cvv, card_type, valid, cvv)
    return card_type and valid and cvv

def verify_luhn(credit_card_string, debug=False):
    """Verify via Luhn algorithm whether a credit card number has a valid last digit"""
    credit_card = re.sub(r'[\D]', '', credit_card_string)
    digit_sum = 0
    cc_parity = len(credit_card) % 2
    for i in range(len(credit_card)-1, -1, -1):
        j = int(credit_card[i])
        if (i + 1) % 2 != cc_parity:
            j = j * 2
            if j > 9:
                j = j - 9
        digit_sum = digit_sum + j
    if debug:
        return digit_sum % 10 == 0, "check sum computed = " + str(digit_sum)
    return digit_sum % 10 == 0

def validate_cvv(credit_card_string, cvv):
    """Return true if the length of the CVV is correct for the card. False otherwise"""
    credit_card = re.sub(r'[\D]', '', credit_card_string)
    card_type = credit_card_vendor(credit_card)
    if card_type == "amex":
        return len(str(cvv)) == 4

    if card_type:
        return len(str(cvv)) == 3

    return False

def validate_date(exp_month, exp_year, max_future_year=5):
    """Return true if month/year are greater than current month/exp_year
       and exp_year is less than 4 years in the future
    """
    today = datetime.date.today()
    expires = datetime.date(int(exp_year), int(exp_month), 28)
    return expires > today and int(exp_year) - today.year < max_future_year
