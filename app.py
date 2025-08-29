from flask import Flask, render_template, request, redirect, url_for, flash,session
import MySQLdb
import MySQLdb.cursors
from flask_mysqldb import MySQL
from collections import defaultdict
from datetime import datetime
from werkzeug.security import generate_password_hash
import os
from flask import send_file
import openpyxl
from io import BytesIO
from model import *

app = Flask(__name__)
app.secret_key = 'a3f5ea2691a8e93c05f4e90e1b8ff123'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Yash@123'
app.config['MYSQL_DB'] = 'banking_products'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)




mysql = MySQL(app)
# mysql.init_app(app)

@app.route('/')
def home():
    return render_template('index.html')



@app.route('/exploreproduct')
def exploreproduct():
    return render_template('ExploreP.html')

#Accounts

@app.route('/Accounts')
def Accounts():
    return render_template('accounts.html')

@app.route('/saving')
def saving():
    return render_template('saving.html')

@app.route('/salary')
def salary():
    return render_template('salary.html')

@app.route('/current')
def current():
    return render_template('current.html')

@app.route('/safec')
def safec():
    return render_template('safec.html')

@app.route('/pension')
def pension():
    return render_template('pension.html')

@app.route('/pmjdy')
def pmjdy():
    return render_template('pmjdy.html')


@app.route('/viewaccounts')
def viewaccounts():
    email = session.get('user_email')
    if not email:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get user details
    cur.execute("SELECT user_id, name, pan, email, mobile FROM bank_users WHERE email = %s", (email,))
    user = cur.fetchone()
    grouped_accounts = defaultdict(list)

    if user:
        # Get all bank accounts for this user
        cur.execute("SELECT * FROM accounts WHERE user_id = %s", (user['user_id'],))
        accounts = cur.fetchall()
        for acc in accounts:
            grouped_accounts[acc['account_type']].append(acc)
    else:
        accounts = []

    cur.close()

    return render_template('viewaccounts.html', accounts=accounts, user=user)







@app.route('/viewdeposits')
def viewdeposits():
    email = session.get('user_email')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor to access columns by name
    cur.execute("SELECT user_id, name, pan, email, mobile_no FROM bank_users WHERE email = %s", (email,))
    user = cur.fetchone()
    grouped_deposits = defaultdict(list)

    if user:
         cur.execute("SELECT * FROM deposits WHERE user_id = %s", (user['user_id'],))
         deposits = cur.fetchall()
         for acc in deposits:
            grouped_deposits[acc['account_type']].append(acc)
    else:
        grouped_deposits = []
        
    cur.close()

   
 
    return render_template('viewdeposits.html', grouped_deposits=grouped_deposits,user=user)



#Deposits

@app.route('/deposits')
def deposits():
    return render_template('deposits.html')

@app.route('/digitalfixed')
def digitalfixed():
    return render_template('digitalfixed.html')

@app.route('/fixeddeposits')
def fixeddeposits():
    return render_template('fixeddeposits.html')

#Cards

@app.route('/cards')
def cards():
    return render_template('cards_main.html')

@app.route('/creditcard')
def creditcard():
    return render_template('creditcard.html')
# @app.route('/cardapply')
# def cardapply():
#     return render_template('cardapply.html')
# @app.route('/comparecards')
# def comparecards():
#     return render_template('comparecards.html')

@app.route('/Debitcard')
def Debitcard():
    return render_template('Debitcard.html')

@app.route('/prepaid')
def prepaid():
    return render_template('prepaid.html')


#loans

@app.route('/loans')
def loans():
    return render_template('loans.html')

@app.route('/home_loan')
def home_loan():
    return render_template('home_loan_form.html')
 
@app.route('/personal_loan')
def personal_loan():
    return render_template('Loan_personal.html')
 
@app.route('/Business_loan')
def Business_loan():
    return render_template('Business_Loan.html')

#forex

@app.route('/forex')
def forex():
    return render_template('forex.html')
 
@app.route('/travel_forex')
def travel_forex():
    return render_template('travel_forex.html')
 
@app.route('/travel_forex_form')
def travel_forex_form():
    return render_template('travel-forex-form.html')
 
@app.route('/send_money_abroad')
def send_money_abroad():
    return render_template('send_money_abroad.html')
 
@app.route('/send_money_abroad_form')
def send_money_abroad_form():
    return render_template('send-money-abroad-form.html')
 
@app.route('/send_money_india')
def send_money_india():
    return render_template('send_money_india.html')  
 
@app.route('/send_money_india_form')
def send_money_india_form():
    return render_template('send-money-india-form.html')    
 
@app.route('/currency_exchange')
def currency_exchange():
    return render_template('currency_exchange.html')
 
@app.route('/currency_exchange_form')
def currency_exchange_form():
    return render_template('currency-exchange-form.html')

#investments

@app.route('/invest')
def invest():
    return render_template('invest.html')

@app.route('/pfinvest')
def pfinvest():
    return render_template('pfinvest.html')


from MySQLdb.cursors import DictCursor

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor(DictCursor)  
        cur.execute("SELECT * FROM bank_users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_email'] = user['email']
            session['user_role'] = user['role'] 
            session['user_id'] = user['user_id']  
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')


import random
import string


def generate_user_id():
    """
    Generate a unique customer ID:
      - Always starts with 'DB'
      - Followed by 6 random digits
    """
    prefix = "DB"
    suffix = ''.join(random.choice(string.digits) for _ in range(6))
    return prefix + suffix


import random

def generate_unique_account_no(account_type):
    """
    Generate a unique deposit account number:
    - Starts with 'DIGIS' if account_type is 'saving'
    - Starts with 'DIGIC' if account_type is 'current'
    """
    prefix_map = {
        'saving': 'DIGIS',
        'current': 'DIGIC',
        'pension' :'DIGIP',
        'salary' : 'DIGISL',
        'safec' : 'DIGISC',
        'penAcc': 'DIGIP',
        'pmjdy' : 'DGIPM'
    }

    prefix = prefix_map.get(account_type.lower())
    if not prefix:
        raise ValueError("account_type must be 'saving' or 'current'")

    cur = mysql.connection.cursor()
    while True:
        suffix = f"{random.randint(0, 9999999999):010d}"
        account_number = prefix + suffix
        cur.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
        if not cur.fetchone():
            break

    return account_number

def generate_deposit_account_no(account_type):
    """
    Generate a unique deposit account number:
    - Starts with 'DIGIS' if account_type is 'saving'
    - Starts with 'DIGIC' if account_type is 'current'
    """
    prefix_map = {
        'digital fixed': 'DIGIDFD',
        'fixed': 'DIGIFD',
        'recurring' :'DIGIRD'
        
    }

    prefix = prefix_map.get(account_type.lower())
    if not prefix:
        raise ValueError("account_type must be 'saving' or 'current'")

    cur = mysql.connection.cursor()
    while True:
        suffix = f"{random.randint(0, 9999999999):010d}"
        account_number = prefix + suffix
        cur.execute("SELECT * FROM deposits WHERE account_number = %s", (account_number,))
        if not cur.fetchone():
            break

    return account_number

def generate_card_number(card_subtype):
    """
    Generate a unique card number:
    - Starts with 'DGVISA' for Visa cards
    - Starts with 'DGMC' for MasterCard
    - Starts with 'DGUPI' for UPI-linked cards
    """
    prefix_map = {
        'visa': 'DGVI',
        'mastercard': 'DGMC',
        'rupay': 'DGRP'
    }

    prefix = prefix_map.get(card_subtype.lower())
    if not prefix:
        raise ValueError("card_type must be 'visa', 'mastercard', or 'rupay'")

    cur = mysql.connection.cursor()
    while True:
        # Generate 10 random digits
        suffix = f"{random.randint(0, 9999999999):016d}"
        card_number = prefix + suffix
        cur.execute("SELECT * FROM bank_ccards WHERE card_number = %s", (card_number,))
        if not cur.fetchone():
            break

    return card_number


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['fname']
        pan = request.form['pan']
        email = request.form['email']
        mobile_no = request.form['mn']
        password = request.form['password']

        cur = mysql.connection.cursor()

        # Check if email or mobile already exists
        cur.execute("SELECT * FROM bank_users WHERE email = %s OR mobile_no = %s", (email, mobile_no))
        if cur.fetchone():
            flash('Email or mobile number already registered', 'danger')
        else:
            # Generate a unique cust_id
            while True:
                user_id = generate_user_id()
                cur.execute("SELECT * FROM bank_users WHERE user_id = %s", (user_id,))
                if not cur.fetchone():  # If not found, it's unique
                    break

            # Insert user with the generated cust_id
            cur.execute(
                "INSERT INTO bank_users (user_id, name,pan, email, mobile_no, password) VALUES (%s, %s,%s, %s, %s, %s)",
                (user_id, name,pan, email, mobile_no, password)
            )
            mysql.connection.commit()
            cur.close()
            
            flash('Welcome ! Please log in.', 'success')
            return redirect(url_for('login'))

        cur.close()

    return render_template('signup.html')

@app.route('/savingform')
def savingform():
    return render_template('savingform.html')

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan, mobile, email,department,aadhaar FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
   
    return render_template("profile.html", user=user)


from datetime import datetime

@app.route('/open_account', methods=['GET', 'POST'])
def open_account():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('userlogin'))  # consistent redirect

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT user_id, name, pan, email, mobile
        FROM bank_users
        WHERE email = %s
    """, (email,))
    user = cur.fetchone()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('userlogin'))  # consistent redirect

    user_id = user['user_id']

    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        aadhar = request.form['aadhar']
        account_type = request.form['accountType']

        # Generate unique account number
        account_number = generate_unique_account_no(account_type)

        cur = mysql.connection.cursor()
        date_of_opening = datetime.now()
        cur.execute("""
            INSERT INTO accounts (
                user_id, first_name, middle_name, last_name, email,
                mobile, aadhar, account_type, account_number,date_of_opening
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """, (
            user_id, first_name, middle_name, last_name, email,
            mobile, aadhar, account_type, account_number,date_of_opening
        ))
        mysql.connection.commit()
        cur.close()

        flash(f"Savings account created. Account number: {account_number}", "success")
        return redirect(url_for('dashboard'))

    return render_template('applicationform1.html', user=user)

from collections import defaultdict

ACCOUNT_TABLES = {
    'saving': 'saving_accounts',
    'current': 'current_accounts',
    'salary': 'salary_accounts',
    'pmjdy': 'pmjdy_accounts',
    'pension': 'pension_accounts',
    'safecustody': 'safecustody_accounts',
 
    # common aliases that map to safecustody
    'safec': 'safecustody_accounts',
    'safe': 'safecustody_accounts'
}
ACCOUNT_TYPES_CANON = set(ACCOUNT_TABLES.keys())
 
def canon_type(t):
    """Normalize incoming accountType values from forms."""
    if not t:
        return None
    t = t.strip().lower()
    if t in ('safe custody', 'safe_custody', 'safec', 'safe'):
        t = 'safecustody'
    return t

# ------------------------- Account Query Helpers (UPDATED) -------------------------
def find_account_by_number(account_number, for_update=False):
    """
    Look up an account by number across all account tables.
    Returns dict: {table_name, account_type, account_number, balance, user_id}
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    for tbl in dict.fromkeys(ACCOUNT_TABLES.values()):
        sql = f"SELECT '{tbl}' AS table_name, account_type, account_number, balance, user_id FROM {tbl} WHERE account_number=%s"
        if for_update:
            sql += " FOR UPDATE"
        cur.execute(sql, (account_number,))
        row = cur.fetchone()
        if row:
            cur.close()
            return row
    cur.close()
    return None
 
def update_account_balance(table_name, account_number, new_balance):
    cur = mysql.connection.cursor()
    cur.execute(f"UPDATE {table_name} SET balance=%s WHERE account_number=%s", (str(new_balance), account_number))
    cur.close()
 
def get_accounts_for_email(email):
    """
    Return list of user's accounts across all tables with:
    {account_type, account_number, balance, table_name}
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    unions = []
    params = []
    for tbl in dict.fromkeys(ACCOUNT_TABLES.values()):
        unions.append(f"""
            SELECT a.account_type, a.account_number, COALESCE(a.balance, 0.00) AS balance, '{tbl}' AS table_name
            FROM {tbl} a
            JOIN bank_users u ON u.user_id = a.user_id
            WHERE u.email = %s
        """)
        params.append(email)
 
    sql = " UNION ALL ".join(unions) + " ORDER BY account_type, account_number"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close()
    return rows
 
def get_account_numbers_for_email(email):
    """Return list of account_numbers owned by email across all tables."""
    accts = get_accounts_for_email(email)
    return [a['account_number'] for a in accts]
 
def generate_transaction_id():
    prefix = "TXN" + datetime.now().strftime("%Y%m%d")
    suffix = ''.join(random.choice(string.digits) for _ in range(6))
    return prefix + suffix
 
 

from decimal import Decimal, InvalidOperation
@app.route('/accountbal')
def accountbal():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    accts = get_accounts_for_email(email)
    total = sum((Decimal(str(acc['balance'])) if acc['balance'] is not None else Decimal('0.00')) for acc in accts)
 
    # pass user
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
 
    return render_template('balance.html', accounts=accts, total_balance=total, user=user) 

@app.route('/Txnhistory')
def Txnhistory():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    my_accts = get_account_numbers_for_email(email)
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    txns = []
    if my_accts:
        placeholders = ','.join(['%s'] * len(my_accts))
        query = f"""
            SELECT id, transaction_id, from_account, to_account, amount, note, status, created_at
            FROM transactions
            WHERE from_account IN ({placeholders}) OR to_account IN ({placeholders})
            ORDER BY created_at DESC, id DESC
            LIMIT 200
        """
        cur.execute(query, tuple(my_accts + my_accts))
        txns = cur.fetchall()
 
    # pass user for header
    cur.execute("SELECT * FROM bank_users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
 
    return render_template('transactions.html', transactions=txns, my_accounts=set(my_accts), user=user)

 
@app.route('/quicktransfer', methods=['GET', 'POST'])
def quicktransfer():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        my_accounts = get_accounts_for_email(email)
        # pass user for header
        cur2 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur2.execute("SELECT * FROM bank_users WHERE email=%s", (email,))
        user = cur2.fetchone()
        cur2.close()
        return render_template('quicktransfer.html', my_accounts=my_accounts, user=user)
 
    # POST: perform transfer
    from_account = request.form.get('from_account')
    to_account   = request.form.get('to_account')
    amount_str   = request.form.get('amount')
    note         = (request.form.get('note') or '').strip()[:255]
 
    if not from_account or not to_account or not amount_str:
        flash('Please provide source, destination, and amount.', 'danger')
        return redirect(url_for('quicktransfer'))
 
    if from_account == to_account:
        flash('Source and destination accounts cannot be the same.', 'danger')
        return redirect(url_for('quicktransfer'))
 
    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            raise InvalidOperation()
    except (InvalidOperation, TypeError):
        flash('Amount must be a positive number.', 'danger')
        return redirect(url_for('quicktransfer'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    txn_id = None
    try:
        mysql.connection.begin()
 
        # who am I
        cur.execute("SELECT user_id FROM bank_users WHERE email=%s", (email,))
        me = cur.fetchone()
        if not me:
            raise ValueError("User not found.")
        my_user_id = me['user_id']
 
        # Lock rows in their specific tables
        src = find_account_by_number(from_account, for_update=True)
        dst = find_account_by_number(to_account, for_update=True)
 
        if not src:
            raise ValueError("Source account not found.")
        if not dst:
            raise ValueError("Destination account not found.")
 
        # Ensure source belongs to logged-in user
        if src['user_id'] != my_user_id:
            raise ValueError("You can only transfer from your own account.")
 
        # Balance check
        if Decimal(str(src['balance'])) < amount:
            raise ValueError("Insufficient balance.")
 
        new_src_bal = Decimal(str(src['balance'])) - amount
        new_dst_bal = Decimal(str(dst['balance'])) + amount
 
        update_account_balance(src['table_name'], from_account, new_src_bal)
        update_account_balance(dst['table_name'], to_account,   new_dst_bal)
 
        txn_id = generate_transaction_id()
        cur.execute("""
            INSERT INTO transactions (transaction_id, from_account, to_account, amount, note, status)
            VALUES (%s, %s, %s, %s, %s, 'success')
        """, (txn_id, from_account, to_account, str(amount), note))
 
        mysql.connection.commit()
        flash(f'Transfer successful: ₹{amount} to {to_account} | Transaction ID: {txn_id}', 'success')
        return redirect(url_for('Txnhistory'))
 
    except Exception as e:
        mysql.connection.rollback()
        # log failure (best effort)
        try:
            if not txn_id:
                txn_id = generate_transaction_id()
            cur.execute("""
                INSERT INTO transactions (transaction_id, from_account, to_account, amount, note, status)
                VALUES (%s, %s, %s, %s, %s, 'failed')
            """, (txn_id, from_account, to_account, str(amount_str or '0'), f'FAILED: {note}' if note else 'FAILED'))
            mysql.connection.commit()
        except Exception:
            mysql.connection.rollback()
        flash(f"Transfer failed: {str(e)}", 'danger')
        return redirect(url_for('quicktransfer'))
    finally:
        cur.close()

 
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    email = session.get('user_email')
    if not email:
        flash("Please login first", "danger")
        return redirect(url_for("login"))
 
    # Fetch user accounts
    my_accounts = get_accounts_for_email(email)
 
    if request.method == "POST":
        to_account = request.form.get("to_account")
        re_to_account = request.form.get("re_to_account")
        amount_str = request.form.get("amount")
        remark = request.form.get("remark")
 
        if to_account != re_to_account:
            flash("Account numbers do not match!", "danger")
            return redirect(url_for("deposit"))
 
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise InvalidOperation()
        except (InvalidOperation, TypeError):
            flash("Please enter a valid positive amount.", "danger")
            return redirect(url_for("deposit"))
 
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        txn_id = None
        try:
            mysql.connection.begin()
 
            # Lock destination account
            dst = find_account_by_number(to_account, for_update=True)
            if not dst:
                raise ValueError("Destination account not found.")
 
            new_balance = Decimal(str(dst["balance"])) + amount
            update_account_balance(dst['table_name'], to_account, new_balance)
 
            # Record transaction (CREDIT only)
            txn_id = generate_transaction_id()
            cur.execute("""
                INSERT INTO transactions (transaction_id, from_account, to_account, amount, note, status)
                VALUES (%s, NULL, %s, %s, %s, 'success')
            """, (txn_id, to_account, str(amount), remark or "Deposit"))
 
            mysql.connection.commit()
            flash(f"Successfully deposited ₹{amount} to account {to_account}. Transaction ID: {txn_id}", "success")
            return redirect(url_for("Txnhistory"))
 
        except Exception as e:
            mysql.connection.rollback()
            try:
                if not txn_id:
                    txn_id = generate_transaction_id()
                cur.execute("""
                    INSERT INTO transactions (transaction_id, from_account, to_account, amount, note, status)
                    VALUES (%s, NULL, %s, %s, %s, 'failed')
                """, (txn_id, to_account or '', str(amount_str or '0'), f'FAILED: {remark}' if remark else 'FAILED'))
                mysql.connection.commit()
            except Exception:
                mysql.connection.rollback()
            flash(f"Deposit failed: {str(e)}", "danger")
            return redirect(url_for("deposit"))
        finally:
            cur.close()
 
    return render_template("deposit.html", accounts=my_accounts)
 

@app.route('/open_deposits', methods=['GET', 'POST'])
def open_deposits():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('userlogin'))  # consistent redirect

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT user_id, name, pan, email, mobile_no
        FROM bank_users
        WHERE email = %s
    """, (email,))
    user = cur.fetchone()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    user_id = user['user_id']

    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        aadhar = request.form['aadhar']
        account_type = request.form['accountType']

        # Generate unique account number
        account_number = generate_deposit_account_no(account_type)

        cur = mysql.connection.cursor()
        date_of_opening = datetime.now()
        cur.execute("""
            INSERT INTO deposits (
                user_id, first_name, middle_name, last_name, email,
                mobile, aadhar, account_type, account_number,date_of_opening
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """, (
            user_id, first_name, middle_name, last_name, email,
            mobile, aadhar, account_type, account_number,date_of_opening
        ))
        mysql.connection.commit()
        cur.close()

        flash(f"Deposit account created. Account number: {account_number}", "success")
        return redirect(url_for('dashboard'))

    return render_template('depositform.html',user=user)



@app.route('/dashboard')
def dashboard():
    role = session.get('user_role')
    email = session.get('user_email')

    if not role or not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    # Fetch the full user details
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    templates = {
        'User': 'userdashboard.html',
        'tl': 'TLdashboard.html',
        'manager': 'managerdashboard.html',
        'Card_Agent': 'cardagent_dashboard.html',
        'Loan_Agent': 'loanagent_dashboard.html'
    }

    return render_template(templates.get(role, 'login.html'), user=user)


#Manager Dasboard Routes

@app.route('/manageaccounts')
def manageaccounts():
    return render_template('manageaccounts.html')

@app.route('/manprofile')
def manprofile():
    return render_template('manprofile.html')

@app.route('/managerapprovals')
def managerapprovals():
    return render_template('managerapprove.html')

@app.route('/manage_accounts')
def manage_accounts():
    return render_template('manage-accounts.html')

@app.route('/manview_deposits')
def manview_deposits():
    return render_template('manviewdeposits.html')

@app.route('/manage_loans')
def manage_loans():
    return render_template('manage-loans.html')

@app.route('/view_investments')
def view_investments():
    return render_template('view-investments.html')

@app.route('/view_cards')
def view_cards():
    return render_template('view-cards.html')

@app.route('/transactions_review')
def transactions_review():
    return render_template('transactions-review.html')

@app.route('/manreport')
def manreport():
    return render_template('manreports.html')

@app.route('/manstaff')
def manstaff():
    return render_template('staff-management.html')

@app.route('/branchperformance')
def branchperformance():
    return render_template('branch-performance.html')


# TL Dashboard Routes


def generate_user_id(department):
    prefixes = {
        "Cards": "CA",
        "Loans": "LN",
        "Investment": "IV",
        "Forex": "FX"
    }
    prefix = prefixes.get(department, "AG")
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT MAX(id) AS max_id FROM agents WHERE department=%s", (department,))
    result = cur.fetchone()
    next_id = (result['max_id'] or 0) + 1
    return f"{prefix}{next_id:03d}"

    # Cards Page
@app.route('/tlcards')
def tlcards():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT user_id, name, department, onboarding_date
        FROM agents
        WHERE status='active' AND department='Cards'
    """)
    agents = cur.fetchall()
    return render_template("tlcards.html", agents=agents)

 # Add User Page
@app.route('/tladduser', methods=['GET', 'POST'])
def tladduser():
    if request.method == 'POST':
        data = request.form
        plain_pw = data['password']
        user_id = generate_user_id(data['department'])
 
        # Auto-generate email
        email = f"{user_id}@digibank.com"
 
        # Assign role based on department
        roles = {
            "Cards": "Card_Agent",
            "Loans": "Loan_Agent",
            "Investment": "Investment_Agent",
            "Forex": "Forex_Agent"
        }
        role = roles.get(data['department'], "agent")
 
        # Handle file upload
        photo = request.files['photo']
        photo_path = ''
        if photo and photo.filename:
            filename = f"{user_id}_{photo.filename}"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            photo.save(photo_path)
 
        # Insert into agents
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            INSERT INTO agents (
                user_id, name, dob, gender, pan, aadhaar, mobile, email,
                date_of_joining, country, state, city, department, photo_path,
                password, role, status, onboarding_date
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id, data['name'], data['dob'], data['gender'],
            data['pan'], data['aadhaar'], data['mobile'], email,
            data['date_of_joining'], data['country'], data['state'], data['city'],
            data['department'], photo_path, plain_pw, role, "active", datetime.now()
        ))
 
        # Insert into users
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            INSERT INTO bank_users (
                user_id, name, dob, gender, pan, aadhaar, mobile, email,
                 country, state, city, department, 
                password, role, status, onboarding_date
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id, data['name'], data['dob'], data['gender'],
            data['pan'], data['aadhaar'], data['mobile'], email,
            data['country'], data['state'], data['city'],
            data['department'], plain_pw, role, "active", datetime.now()
        ))
 
        mysql.connection.commit()
 
        # Redirect to department page
        if data['department'] == "Cards":
            return redirect(url_for('tlcards'))
        elif data['department'] == "Loans":
            return redirect(url_for('tlloan'))
        elif data['department'] == "Investment":
            return redirect(url_for('tlinvest'))
        elif data['department'] == "Forex":
            return redirect(url_for('tlforex'))
        else:
            return redirect(url_for('dashboard'))
 
    return render_template("tladduser.html")


@app.route('/download_excel')
def download_excel():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM agents")
    members = cur.fetchall()

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Agent Details"

    sheet.append([
        "ID", "Agent Id", "First Name", "Last Name", "Dob", "Gender", "Pan Card",
        "Aadhaar Card", "Date of Joining", "Country", "State", "City", "Department", 
        "Status", "Onboarding Date", "Deleted Date"
    ])

    for member in members:
        sheet.append([
            member["id"],
            member["user_id"],
            member["name"],
            
            member["dob"],
            member["gender"],
            member["pan"],
            member["aadhaar"],
            member["date_of_joining"],
            member["country"],
            member["state"],
            member["city"],
            member["department"],
            member["status"],
            member["onboarding_date"].strftime("%Y-%m-%d %H:%M:%S") if member["onboarding_date"] else "",
            member["deleted_date"].strftime("%Y-%m-%d %H:%M:%S") if member["deleted_date"] else ""
        ])

    file_stream = BytesIO()
    workbook.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        download_name='agents.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



@app.route('/tldeleteuser', methods=['GET', 'POST'])

def tldeleteuser():

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    if request.method == 'POST':

        ids = request.form.getlist('selected_ids')

        for id in ids:

            # update both tables

            cur.execute("UPDATE agents SET status='deleted', deleted_date=%s WHERE user_id=%s", (datetime.now(), id))

            cur.execute("UPDATE bank_users SET status='deleted', deleted_date=%s WHERE user_id=%s", (datetime.now(), id))

        mysql.connection.commit()

        cur.close()

        flash("Selected users deleted successfully", "success")

        return redirect(url_for('dashboard'))
 
    # Filtering logic

    department = request.args.get('department')

    if department:

        cur.execute("""

            SELECT user_id, name, department, onboarding_date 

            FROM agents WHERE status='active' AND department=%s

        """, (department,))

    else:

        cur.execute("""

            SELECT user_id, name, department, onboarding_date 

            FROM agents WHERE status='active'

        """)

    agents = cur.fetchall()

    cur.close()
 
    return render_template("tldeleteuser.html", agents=agents)

 

   


# Loan Page
@app.route('/tlloan')
def tlloan():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT user_id,name, department, onboarding_date 
        FROM agents 
        WHERE status='active' AND department='Loans'
    """)
    agents = cur.fetchall()
    return render_template("tlloan.html", agents=agents)

# Invest Page
@app.route('/tlinvest')
def tlinvest():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT user_id, name, department, onboarding_date 
        FROM agents 
        WHERE status='active' AND department='Investment'
    """)
    agents = cur.fetchall()
    return render_template("tlinvest.html", agents=agents)

# Forex Page
@app.route('/tlforex')
def tlforex():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT user_id, name, department, onboarding_date 
        FROM agents 
        WHERE status='active' AND department='Forex'
    """)
    agents = cur.fetchall()
    return render_template("tlforex.html", agents=agents)

# Team Analysis Page
@app.route('/teamanalysis')
def teamanalysis():
    return render_template("teamanalysis.html")

#User Dashboard- cards

@app.route('/open_cards', methods=['GET', 'POST'])
def open_cards():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('userlogin'))  # consistent redirect

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT cust_id, name, pan, email, mobile_no
        FROM users
        WHERE email = %s
    """, (email,))
    user = cur.fetchone()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('userlogin'))

    cust_id = user['cust_id']

    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        Addhar = request.form['Addhar']
        card_type = request.form['card_type']
        card_subtype = request.form['card_subtype']

        # Generate unique card number
        card_number = generate_card_number(card_subtype)

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO bank_ccards (
    cust_id, first_name, middle_name, last_name, email,
    mobile, Addhar, card_type, card_subtype, card_number
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cust_id, first_name, middle_name, last_name, email,
            mobile, Addhar, card_type,card_subtype, card_number
        ))
        mysql.connection.commit()
        cur.close()

        flash(f"{card_type.capitalize()} card created. Card number: {card_number}", "success")
        return redirect(url_for('dashboard'))

    return render_template('usercardform.html', user=user)


@app.route('/userdebitform')
def userdebitform():
    return render_template('userdebitform.html')

@app.route('/userprepaidform')
def userprepaidform():
    return render_template('userprepaidform.html')


@app.route('/paybill')
def paybill():
    return render_template('paybill.html')



@app.route('/banktransfer')
def banktransfer():
    return render_template('banktransfer.html')






#Dashboard - user->loan

@app.route('/userdashloan')
def userdashloan():
    return render_template('userdashloans.html')
   




@app.route('/logout')
def logout():
    return render_template('index.html')

#Agent Dashboard(Card_Agent)

@app.route('/agentprofile')
def agentprofile():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan,dob, mobile, email,city,state,country,gender,department,status,role,password,aadhaar,deleted_date FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()

    return render_template('agentprofile.html',user=user)

@app.route('/updateprofile')
def updateprofile():
    return render_template('updateprofile.html')

@app.route('/cardapplications')
def cardapplications():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan,dob, mobile, email,city,state,country,gender,department,status,role,password,aadhaar,deleted_date FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('cardapplications.html',user=user)
@app.route('/applycardagent')
def applycardagent():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan,dob, mobile, email,city,state,country,gender,department,status,role,password,aadhaar,deleted_date FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('applycard.html',user=user)

@app.route('/cardperformance')
def cardperformance():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('cardperformance.html',user=user)


#Loan Agent Dashboard

@app.route('/loanagentprofile')
def loanagentprofile():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan,dob, mobile, email,city,state,country,gender,department,status,role,password,aadhaar,deleted_date FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()

    return render_template('agentprofile.html',user=user)

@app.route('/agentapplyloan')
def agentapplyloan():

    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('agentapplyloan.html',user=user)

@app.route('/agentloanapproval')
def agentloanapproval():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('agentloanapproval.html',user=user)

@app.route('/loanperformance')
def loanperformance():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('loanperformance.html',user=user)

   
if __name__ == '__main__':
    app.run(debug=True)
