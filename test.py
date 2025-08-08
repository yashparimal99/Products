import random

type=input("Enter type:")

def generate_unique_account_no(account_type):
    """
    Generate an account number with a prefix:
    - "DIGIS" for saving accounts
    - "DIGIC" for current accounts
    """
    prefix_map = {
        'saving': 'DIGIS',
        'current': 'DIGIC'
    }
    prefix = prefix_map.get(account_type.lower())
    if not prefix:
        raise ValueError("account_type must be 'saving' or 'current'")

    suffix = f"{random.randint(0, 9999999999):010d}"
    account_number = prefix + suffix
    return account_number
    
print(generate_unique_account_no(type))
