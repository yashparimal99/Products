# import random
# import string
# from app import *
# from extension import mysql


# def generate_cust_id():
#     """
#     Generate a unique customer ID:
#       - Always starts with 'DB'
#       - Followed by 6 random digits
#     """
#     prefix = "DB"
#     suffix = ''.join(random.choice(string.digits) for _ in range(6))
#     return prefix + suffix

# def generate_unique_account_no(account_type):
#     """
#     Generate a unique deposit account number:
#     - Starts with 'DIGIS' if account_type is 'saving'
#     - Starts with 'DIGIC' if account_type is 'current'
#     """
#     prefix_map = {
#         'saving': 'DIGIS',
#         'current': 'DIGIC',
#         'pension' :'DIGIP',
#         'salary' : 'DIGISL',
#         'safec' : 'DIGISC',
#         'penAcc': 'DIGIP',
#         'pmjdy' : 'DGIPM'
#     }

#     prefix = prefix_map.get(account_type.lower())
#     if not prefix:
#         raise ValueError("account_type must be 'saving' or 'current'")

#     cur = mysql.connection.cursor()
#     while True:
#         suffix = f"{random.randint(0, 9999999999):010d}"
#         account_number = prefix + suffix
#         cur.execute("SELECT * FROM bank_accounts WHERE account_number = %s", (account_number,))
#         if not cur.fetchone():
#             break

#     return account_number

# def generate_deposit_account_no(account_type):
#     """
#     Generate a unique deposit account number:
#     - Starts with 'DIGIS' if account_type is 'saving'
#     - Starts with 'DIGIC' if account_type is 'current'
#     """
#     prefix_map = {
#         'digital fixed': 'DIGIDFD',
#         'fixed': 'DIGIFD',
#         'recurring' :'DIGIRD'
        
#     }

#     prefix = prefix_map.get(account_type.lower())
#     if not prefix:
#         raise ValueError("account_type must be 'saving' or 'current'")

#     cur = mysql.connection.cursor()
#     while True:
#         suffix = f"{random.randint(0, 9999999999):010d}"
#         account_number = prefix + suffix
#         cur.execute("SELECT * FROM bank_deposits WHERE account_number = %s", (account_number,))
#         if not cur.fetchone():
#             break

#     return account_number