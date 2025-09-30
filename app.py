from flask import Flask,abort, render_template, request, redirect, url_for, flash,session,jsonify
import MySQLdb
import MySQLdb.cursors
from flask_mysqldb import MySQL
from collections import defaultdict
from datetime import datetime
from werkzeug.security import generate_password_hash
import os
from flask import send_file
from datetime import date
from decimal import Decimal, InvalidOperation
import openpyxl
from io import BytesIO
from model import *
import os, uuid, re, MySQLdb

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
    accounts = []
 
    if user:
        # List of all account tables
        account_tables = [
            "saving_accounts",
            "current_accounts",
            "salary_accounts",
            "pmjdy_accounts",
            "pension_accounts",
            "safecustody_accounts"
        ]
 
        for table in account_tables:
            cur.execute(f"SELECT *, '{table}' as account_type FROM {table} WHERE user_id = %s", (user['user_id'],))
            all_accounts = cur.fetchall()
 
            for acc in all_accounts:
                if acc.get("status_flag") == "R":  # Rejected → skip
                    continue
 
                # Convert DB status → readable
                if acc.get("status_flag") is None:
                    acc["status_text"] = "Pending"
                elif acc.get("status_flag") == "A":
                    acc["status_text"] = "Approved"
                else:
                    acc["status_text"] = "Pending"
 
                accounts.append(acc)
 
    cur.close()
    return render_template('viewaccounts.html', accounts=accounts, user=user)
 

def months_between(d0: date, d1: date) -> int:
    return max(0, int(years_between(d0, d1) * 12.0))
def calc_fd_current_value(
    principal: Decimal, rate_pct: Decimal, compounding: str,
    tenure_months: int, opened_on: date, asof: date
) -> Decimal:
    """
    Current accrued value for FD/DFD capped at the maturity value.
    """
    if not principal or principal <= 0 or not tenure_months or tenure_months <= 0:
        return Decimal('0.00')
 
    r = float(rate_pct or 0) / 100.0
    n = compounding_periods_per_year(compounding)
    elapsed_years = min(float(tenure_months) / 12.0, years_between(opened_on, asof))
 
    if r == 0.0:
        amt = float(principal)
    else:
        amt = float(principal) * (1.0 + r / n) ** (n * elapsed_years)
 
    return Decimal(str(round(amt, 2)))
 
def calc_rd_value_so_far(
    monthly_installment: Decimal, rate_pct: Decimal,
    opened_on: date, asof: date, tenure_months: int
) -> Decimal:
    """
    Future value of an ordinary annuity with monthly contributions up to 'asof'
    (capped at tenure). Uses monthly rate r/12 for simplicity.
    """
    if not monthly_installment or monthly_installment <= 0:
        return Decimal('0.00')
 
    k = min(tenure_months, months_between(opened_on, asof))
    if k <= 0:
        return Decimal('0.00')

def calc_rd_maturity_value(
    monthly_installment: Decimal, rate_pct: Decimal, tenure_months: int
) -> Decimal:
    """Final value of all installments at maturity (simplified monthly comp)."""
    if not monthly_installment or monthly_installment <= 0 or tenure_months <= 0:
        return Decimal('0.00')
    i = float(rate_pct or 0) / 100.0 / 12.0
    if i == 0.0:
        amt = float(monthly_installment) * tenure_months
    else:
        amt = float(monthly_installment) * (((1.0 + i) ** tenure_months - 1.0) / i)
    return Decimal(str(round(amt, 2)))

def years_between(d0: date, d1: date) -> float:
    return max(0.0, (d1 - d0).days / 365.25)
 
 



 

@app.route('/viewdeposits')
def viewdeposits():
    email = session.get('user_email')
    if not email:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan, email, mobile FROM bank_users WHERE email = %s", (email,))
    user = cur.fetchone()
    today = datetime.utcnow().date()
 
    deposits = []
    if user:
        # Fetch from request_deposits instead of per-table
        cur.execute("""
            SELECT *
            FROM request_deposits
            WHERE email = %s
              AND (status_flag IS NULL OR status_flag = 'A')
            ORDER BY created_at DESC
        """, (email,))
        rows = cur.fetchall()
 
        for row in rows:
            dep_type = row['deposit_type']
            row['account_type'] = dep_type
            row['opened_on'] = row.get('created_at').date() if row.get('created_at') else None
            row['tenure_months'] = int(row.get('tenure_months') or 0)
            row['interest_rate'] = Decimal(str(row.get('interest_rate') or '0'))
            row['compounding'] = (row.get('compounding') or 'QUARTERLY').upper()
            row['months_elapsed'] = months_between(row['opened_on'], today) if row['opened_on'] else 0
            row['months_remaining'] = max(0, row['tenure_months'] - row['months_elapsed'])
 
            # status mapping
            if row['status_flag'] is None:
                row['status_text'] = "Pending"
            elif row['status_flag'] == "A":
                row['status_text'] = "Approved"
            else:
                row['status_text'] = "Unknown"
 
            # Enrich FD / RD values
            if dep_type in ('Fixed Deposit', 'Digital Fixed Deposit'):
                principal = Decimal(str(row.get('principal_amount') or '0'))
                current_value = calc_fd_current_value(
                    principal, row['interest_rate'], row['compounding'],
                    row['tenure_months'], row['opened_on'], today
                )
                maturity_value = row.get('maturity_amount')
                if maturity_value is None:
                    maturity_value = calc_fd_maturity_amount(
                        principal, row['interest_rate'], row['tenure_months'], row['compounding']
                    )
                row['current_balance'] = current_value
                row['maturity_amount'] = maturity_value
 
            elif dep_type == 'Recurring Deposit':
                monthly_inst = Decimal(str(row.get('monthly_installment') or '0'))
                current_value = calc_rd_value_so_far(
                    monthly_inst, row['interest_rate'], row['opened_on'], today, row['tenure_months']
                )
                maturity_value = row.get('maturity_amount')
                if maturity_value is None:
                    maturity_value = calc_rd_maturity_value(
                        monthly_inst, row['interest_rate'], row['tenure_months']
                    )
                row['current_balance'] = current_value
                row['maturity_amount'] = maturity_value
 
            deposits.append(row)
    else:
        deposits = []
 
    cur.close()
    return render_template(
        'viewdeposits.html',
        deposits=deposits,
        user=user,
        as_of=today
    )
  


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

@app.route('/Recurringdeposits')
def Recurringdeposits():
    return render_template('Recurringdeposits.html')

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

# @app.route('/home_loan')
# def home_loan():
#     return render_template('home_loan_form.html')
 
# @app.route('/personal_loan')
# def personal_loan():
#     return render_template('Loan_personal.html')
 
# @app.route('/Business_loan')
# def Business_loan():
#     return render_template('Business_Loan.html')

# ========== USER: VIEW LOANS ==========
 

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
    """Generate globally-unique account number across ALL account tables."""
    prefix_map = {
        'savings': 'DIGIS',
        'current': 'DIGIC',
        'pension': 'DIGIP',
        'salary': 'DIGISL',
        'safecustody': 'DIGISC',
        'pmjdy': 'DGIPM',
        # legacy aliases
        'safec': 'DIGISC',
        'penacc': 'DIGIP'
    }
    t = canon_type(account_type)
    prefix = prefix_map.get(t)
    if not prefix:
        raise ValueError("account_type must be one of: savings/current/pension/salary/safecustody/pmjdy")
 
    cur = mysql.connection.cursor()
    tables = list(dict.fromkeys(ACCOUNT_TABLES.values()))  # unique table names
 
    while True:
        suffix = f"{random.randint(0, 9999999999):010d}"
        account_number = prefix + suffix
 
        # check uniqueness across all account tables
        unique = True
        for tbl in tables:
            cur.execute(f"SELECT 1 FROM {tbl} WHERE account_number = %s", (account_number,))
            if cur.fetchone():
                unique = False
                break
        if unique:
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
        name = request.form['name']
        pan = request.form['pan']
        email = request.form['email']
        dob = request.form['dob']
        aadhaar = request.form['aadhaar']
        gender = request.form['gender']
        mobile = request.form['mobile']
        password = request.form['password']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        onboarding_date = datetime.now()

        cur = mysql.connection.cursor()

        # Check if email or mobile already exists
        cur.execute("SELECT * FROM bank_users WHERE email = %s OR mobile = %s", (email, mobile))
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
                "INSERT INTO bank_users (user_id, name,pan,dob, email, mobile, password,aadhaar,gender,city,state,country,onboarding_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)",
                (user_id, name,pan,dob, email, mobile, password,aadhaar,gender,city,state,country,onboarding_date)
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
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
   
    return render_template("profile.html", user=user)

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # GET → load edit form
    if request.method == 'GET':
        cur.execute("""
            SELECT user_id, name, email, mobile,
                   COALESCE(address,'') AS address,
                   COALESCE(city,'')    AS city,
                   COALESCE(state,'')   AS state,
                   COALESCE(country,'') AS country
            FROM bank_users
            WHERE email=%s
        """, (email,))
        user = cur.fetchone()
        cur.close()
        return render_template('updateprofile.html', user=user)
 
    # POST → save changes
    cur.execute("""
        SELECT mobile, address, city, state, country, password
        FROM bank_users
        WHERE email=%s
    """, (email,))
    current = cur.fetchone()
 
    mobile   = (request.form.get('mobile')   or '').strip()
    address  = (request.form.get('address')  or '').strip()
    city     = (request.form.get('city')     or '').strip()
    state    = (request.form.get('state')    or '').strip()
    country  = (request.form.get('country')  or '').strip()
 
    curr_pw  = (request.form.get('current_password') or '').strip()
    new_pw   = (request.form.get('new_password')     or '').strip()
    conf_pw  = (request.form.get('confirm_password') or '').strip()
 
    updates = {}
 
    # Only update changed & non-empty values
    if mobile and mobile != (current['mobile'] or ''):
        if not (len(mobile) == 10 and mobile.isdigit()):
            flash('Mobile must be exactly 10 digits.', 'danger')
            cur.close()
            return redirect(url_for('update_profile'))
        updates['mobile'] = mobile
    if address and address != (current['address'] or ''):
        updates['address'] = address
    if city and city != (current['city'] or ''):
        updates['city'] = city
    if state and state != (current['state'] or ''):
        updates['state'] = state
    if country and country != (current['country'] or ''):
        updates['country'] = country
 
    # Optional password change
    if curr_pw or new_pw or conf_pw:
        if not current or current['password'] != curr_pw:
            flash('Current password is incorrect.', 'danger')
            cur.close()
            return redirect(url_for('update_profile'))
        if not new_pw or new_pw != conf_pw or len(new_pw) < 8:
            flash('New password mismatch or too short (min 8).', 'danger')
            cur.close()
            return redirect(url_for('update_profile'))
        updates['password'] = new_pw
 
    # Helper: human list join
    def human_join(items):
        if not items:
            return ''
        if len(items) == 1:
            return items[0]
        return ', '.join(items[:-1]) + ' and ' + items[-1]
 
    labels = {
        'mobile': 'mobile number',
        'address': 'address',
        'city': 'city',
        'state': 'state',
        'country': 'country',
        'password': 'password'
    }
 
    try:
        if updates:
            set_clause = ", ".join([f"{k}=%s" for k in updates.keys()])
            params = list(updates.values()) + [email]
            cur.execute(f"UPDATE bank_users SET {set_clause} WHERE email=%s", params)
            mysql.connection.commit()
 
            changed = [labels[k] for k in updates.keys()]
            msg = f"Updated {human_join(changed)}."
            # Make password updates feel more “done”
            if 'password' in updates and len(updates) == 1:
                msg = "Password changed successfully."
            flash(msg, 'success')
        else:
            flash('No changes to update.', 'info')
 
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Couldn't save your changes. Error: {e}", 'danger')
    finally:
        cur.close()
 
    return redirect(url_for('profile'))



from datetime import datetime

def generate_request_id():

    """
    Generate a unique request ID:
    Always starts with 'REQ' + 3 random digits
    """
    prefix = "REQ"
    suffix = ''.join(random.choice(string.digits) for _ in range(3))
    return prefix + suffix

@app.route('/open_account', methods=['GET', 'POST'])
def open_account():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan, email, mobile FROM bank_users WHERE email = %s", (email,))
    user = cur.fetchone()
 
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
 
    user_id = user['user_id']
 
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        aadhar = request.form['aadhar']
        account_type_raw = request.form['accountType']
        account_type = canon_type(account_type_raw)
 
        if account_type not in ACCOUNT_TABLES:
            flash('Invalid account type.', 'danger')
            return redirect(url_for('open_account'))
 
        account_number = generate_unique_account_no(account_type)
        table_name = ACCOUNT_TABLES[account_type]
 
        cur2 = mysql.connection.cursor()
        date_of_opening = datetime.now()
        cur2.execute(f"""
            INSERT INTO {table_name} (
                user_id, first_name, middle_name, last_name, email,
                mobile, aadhar, account_type, account_number, date_of_opening, balance
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, first_name, middle_name, last_name, email,
            mobile, aadhar, account_type, account_number, date_of_opening, Decimal('0.00')
        ))
        mysql.connection.commit()
        cur2.close()
        request_id = generate_request_id()
        cur.execute("""
            INSERT INTO accounts_requests (
                request_id, first_name, middle_name, last_name, email,
                mobile, aadhar, account_type, account_number,request_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """, (
            request_id, first_name, middle_name, last_name, email,
            mobile, aadhar, account_type, account_number,"Open New Account"
        ))
 
        mysql.connection.commit()
        cur2.close()
 
        flash(f"Account created. Account number: {account_number}", "success")
        return redirect(url_for('dashboard'))
 
    cur.close()
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

# === SIMPLE DEPOSIT (credits account + logs to transactions; mirrors to `deposits` ledger) ===
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    email = session.get('user_email')
    if not email:
        flash("Please login first", "danger")
        return redirect(url_for("login"))
 
    my_accounts = get_accounts_for_email(email)  # list of dicts with account_number, account_type, etc.
 
    if request.method == "POST":
        # Single destination account (belongs to the logged-in user)
        to_account  = request.form.get("account_number")
        amount_str  = request.form.get("amount")
        remark      = (request.form.get("remark") or "").strip()
 
        if not to_account or not amount_str:
            flash("Please select an account and enter an amount.", "danger")
            return redirect(url_for("deposit"))
 
        # Ensure the account truly belongs to the current user (prevents tampering)
        my_acc_numbers = {str(acc.get("account_number")) for acc in my_accounts or []}
        if to_account not in my_acc_numbers:
            flash("Invalid account selection.", "danger")
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
        FROM_SENTINEL = 'CASH'  # record as cash deposit
 
        try:
            # get user_id for ledger
            cur.execute("SELECT user_id FROM bank_users WHERE email=%s", (email,))
            me = cur.fetchone()
            if not me:
                raise ValueError("User not found.")
            my_user_id = me['user_id']
 
            # begin tx for balance + transactions
            mysql.connection.begin()
 
            # lock destination account
            dst = find_account_by_number(to_account, for_update=True)
            if not dst:
                raise ValueError("Destination account not found.")
 
            start_bal = Decimal(str(dst["balance"] if dst["balance"] is not None else "0.00"))
            new_balance = start_bal + amount
            update_account_balance(dst['table_name'], to_account, new_balance)
 
            # record transaction (credit only) using sentinel in from_account
            txn_id = generate_transaction_id()
            cur.execute("""
                INSERT INTO transactions (transaction_id, from_account, to_account, amount, note, status)
                VALUES (%s, %s, %s, %s, %s, 'success')
            """, (txn_id, FROM_SENTINEL, to_account, str(amount), remark or "Deposit"))
 
            mysql.connection.commit()
 
        except Exception as e:
            mysql.connection.rollback()
            # best-effort failure record
            try:
                if not txn_id:
                    txn_id = generate_transaction_id()
                cur.execute("""
                    INSERT INTO transactions (transaction_id, from_account, to_account, amount, note, status)
                    VALUES (%s, %s, %s, %s, %s, 'failed')
                """, (txn_id, FROM_SENTINEL, to_account or '', str(amount_str or '0'),
                      f'FAILED: {remark}' if remark else 'FAILED'))
                mysql.connection.commit()
            except Exception:
                mysql.connection.rollback()
            cur.close()
            flash(f"Deposit failed: {str(e)}", "danger")
            return redirect(url_for("deposit"))
 
        # mirror to simple ledger; failure here won't undo the credit
        try:
            cur.execute("""
                INSERT INTO deposits (user_id, account_number, amount, note, txn_id, status)
                VALUES (%s, %s, %s, %s, %s, 'success')
            """, (my_user_id, to_account, str(amount), remark or "Deposit", txn_id))
            mysql.connection.commit()
        except Exception as ledger_err:
            mysql.connection.rollback()
            # keep going; money already credited
            print("Warning: deposits ledger insert failed:", ledger_err)
 
        cur.close()
        flash(f"Successfully deposited ₹{amount} to account {to_account}. Transaction ID: {txn_id}", "success")
        return redirect(url_for("Txnhistory"))
 
    return render_template("deposit.html", accounts=my_accounts)
   
 

DEPOSIT_TABLES = {
    'Digital Fixed Deposit': 'digital_fixed_deposits',
    'Fixed Deposit':        'fixed_deposits',
    'Recurring Deposit':    'recurring_deposits'
}
 
def canon_deposit_type(t: str):
    """Normalize UI/form values to our 3 canonical labels."""
    if not t:
        return None
    s = t.strip().lower()
    if s in ('digital fixed', 'digital fixed deposit', 'digital fd', 'dfd', 'digital', 'digital fixed deposits'):
        return 'Digital Fixed Deposit'
    if s in ('fixed', 'fixed deposit', 'fd', 'fixed deposits'):
        return 'Fixed Deposit'
    if s in ('recurring', 'recurring deposit', 'rd', 'recurring deposits'):
        return 'Recurring Deposit'
    return t.strip()
 
def generate_deposit_account_no(account_type):
    """
    Generate a globally-unique deposit account number across ALL deposit tables.
    Works with canonical types ('Digital Fixed Deposit', 'Fixed Deposit', 'Recurring Deposit')
    and their synonyms via canon_deposit_type().
    """
    dep_type = canon_deposit_type(account_type)
    prefix_map = {
        'Digital Fixed Deposit': 'DIGIDFD',
        'Fixed Deposit':        'DIGIFD',
        'Recurring Deposit':    'DIGIRD'
    }
    prefix = prefix_map.get(dep_type)
    if not prefix:
        raise ValueError("deposit type must be: Digital Fixed Deposit / Fixed Deposit / Recurring Deposit")
 
    cur = mysql.connection.cursor()
    tables = list(DEPOSIT_TABLES.values())
    while True:
        suffix = f"{random.randint(0, 9999999999):010d}"
        account_number = prefix + suffix
        unique = True
        for tbl in tables:
            cur.execute(f"SELECT 1 FROM {tbl} WHERE account_number=%s", (account_number,))
            if cur.fetchone():
                unique = False
                break
        if unique:
            break
    return account_number
 
def compounding_periods_per_year(comp: str) -> int:
    return {'MONTHLY': 12, 'QUARTERLY': 4, 'HALF_YEARLY': 2, 'YEARLY': 1}.get((comp or 'QUARTERLY').upper(), 4)
 
def calc_fd_maturity_amount(principal: Decimal, annual_rate_pct: Decimal,
                            tenure_months: int, compounding: str) -> Decimal:
    if principal is None or annual_rate_pct is None or tenure_months is None:
        return None
    if principal <= 0 or tenure_months <= 0:
        return None
    r = float(annual_rate_pct) / 100.0
    n = compounding_periods_per_year(compounding)
    t_years = float(tenure_months) / 12.0
    if r == 0.0:
        return principal.quantize(Decimal('0.01'))
    amount = float(principal) * (1.0 + r/n) ** (n*t_years)
    return Decimal(str(round(amount, 2)))

def generate_deposit_request_id():
    """
    DEP + 4 random digits, unique in request_deposits.
    """
    cur = mysql.connection.cursor()
    while True:
        rid = "DEP" + f"{random.randint(0, 9999):04d}"
        cur.execute("SELECT 1 FROM request_deposits WHERE request_id=%s", (rid,))
        if not cur.fetchone():
            break
    cur.close()
    return rid
 
 
 


@app.route('/open_deposits', methods=['GET', 'POST'])
def open_deposits():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan, email, mobile FROM bank_users WHERE email = %s", (email,))
    user = cur.fetchone()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
    user_id = user['user_id']
 
    if request.method == 'POST':
        # KYC
        first_name  = request.form['first_name']
        middle_name = request.form.get('middle_name', '')
        last_name   = request.form['last_name']
        email    = request.form['email']
        mobile      = request.form['mobile']
        aadhar      = request.form['aadhar']
 
        # Normalize deposit type and map to table
        dep_type_raw = request.form['accountType']
        dep_type = canon_deposit_type(dep_type_raw)
        if dep_type not in DEPOSIT_TABLES:
            flash('Invalid deposit type.', 'danger')
            return redirect(url_for('open_deposits'))
        table_name = DEPOSIT_TABLES[dep_type]
 
        # Generate unique numbers
        account_number = generate_deposit_account_no(dep_type)
        request_id = generate_deposit_request_id()   # <-- new (DEP####)
 
        # Fixed, unchangeable interest rate (6%)
        interest_rate = Decimal('6')
 
        # Common inputs
        compounding = (request.form.get('compounding') or 'QUARTERLY').upper()
        tenure_str = request.form.get('tenure_months', '12')
        try:
            tenure_months = int(tenure_str)
            if tenure_months <= 0:
                raise InvalidOperation()
        except Exception:
            flash('Please enter a valid tenure (months).', 'danger')
            return redirect(url_for('open_deposits'))
 
        cur2 = mysql.connection.cursor()
 
        if dep_type in ('Fixed Deposit', 'Digital Fixed Deposit'):
            principal_str = request.form.get('principal_amount', '').strip()
            try:
                principal = Decimal(principal_str)
                if principal <= 0:
                    raise InvalidOperation()
            except Exception:
                flash('Principal amount must be positive for FD.', 'danger')
                return redirect(url_for('open_deposits'))
 
            maturity_amount = calc_fd_maturity_amount(principal, interest_rate, tenure_months, compounding)
 
            # 1) Insert into deposit table
            cur2.execute(f"""
                INSERT INTO {table_name} (
                    user_id, first_name, middle_name, last_name, email, mobile, aadhar,
                    account_number, principal_amount, interest_rate, compounding, tenure_months,
                    maturity_amount, status_flag
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NULL)
            """, (
                user_id, first_name, middle_name, last_name, email, mobile, aadhar,
                account_number, str(principal), str(interest_rate), compounding, tenure_months,
                maturity_amount
            ))
 
            # 2) Insert into request_deposits
            cur2.execute("""
                INSERT INTO request_deposits (
                    request_id, deposit_type, account_number,
                    first_name, middle_name, last_name, email, mobile, aadhar,
                    principal_amount, interest_rate, compounding, tenure_months, maturity_amount,
                    request_type, status_flag
                ) VALUES (%s,%s,%s,
                          %s,%s,%s,%s,%s,%s,
                          %s,%s,%s,%s,%s,
                          'Open New Deposit', NULL)
            """, (
                request_id, dep_type, account_number,
                first_name, middle_name, last_name, email, mobile, aadhar,
                str(principal), str(interest_rate), compounding, tenure_months, maturity_amount
            ))
 
        elif dep_type == 'Recurring Deposit':
            install_str = request.form.get('monthly_installment', '').strip()
            try:
                monthly_installment = Decimal(install_str)
                if monthly_installment <= 0:
                    raise InvalidOperation()
            except Exception:
                flash('Monthly installment must be positive for RD.', 'danger')
                return redirect(url_for('open_deposits'))
 
            # 1) Insert into deposit table
            cur2.execute(f"""
                INSERT INTO {table_name} (
                    user_id, first_name, middle_name, last_name, email, mobile, aadhar,
                    account_number, monthly_installment, interest_rate, compounding, tenure_months,
                    maturity_amount, status_flag
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NULL, NULL)
            """, (
                user_id, first_name, middle_name, last_name, email, mobile, aadhar,
                account_number, str(monthly_installment), str(interest_rate), compounding, tenure_months
            ))
 
            # 2) Insert into request_deposits
            cur2.execute("""
                INSERT INTO request_deposits (
                    request_id, deposit_type, account_number,
                    first_name, middle_name, last_name, email, mobile, aadhar,
                    monthly_installment, interest_rate, compounding, tenure_months, maturity_amount,
                    request_type, status_flag
                ) VALUES (%s,%s,%s,
                          %s,%s,%s,%s,%s,%s,
                          %s,%s,%s,%s,NULL,
                          'Open New Deposit', NULL)
            """, (
                request_id, dep_type, account_number,
                first_name, middle_name, last_name, email, mobile, aadhar,
                str(monthly_installment), str(interest_rate), compounding, tenure_months
            ))
 
        mysql.connection.commit()
        cur2.close()
       
        flash(f"{dep_type} application submitted (pending approval). A/C: {account_number}", "success")
        return redirect(url_for('dashboard'))
 
    cur.close()
    return render_template('depositform.html', user=user)
 


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
        'Loan_Agent': 'loanagent_dashboard.html',
        'Investment_Agent': 'investagent_dashboard.html'
    }
 
    if role == "manager":
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
        # Total customers
        cur.execute("SELECT COUNT(*) AS total_customers FROM bank_users WHERE role = 'User'")
        total_customers = cur.fetchone()['total_customers']
 
        # Pending requests
        cur.execute("SELECT COUNT(*) AS c FROM accounts_requests WHERE status_flag IS NULL")
        acc_count = cur.fetchone()['c']
 
        cur.execute("SELECT COUNT(*) AS c FROM request_deposits WHERE status_flag IS NULL")
        dep_count = cur.fetchone()['c']
 
        cur.execute("SELECT COUNT(*) AS c FROM loan_requests WHERE status = 'pending_manager'")
        loan_count = cur.fetchone()['c']
 
        cur.execute("SELECT COUNT(*) AS c FROM card_requests WHERE status_flag IS NULL")
        card_count = cur.fetchone()['c']
 
        cur.execute("SELECT COUNT(*) AS c FROM investment_applications WHERE status = 'pending_manager'")
        invest_count = cur.fetchone()['c']
 
        total_pending = acc_count + dep_count + loan_count + card_count + invest_count
 
        # 💰 Total Principal Amount (from request_deposits only)
        cur.execute("SELECT COALESCE(SUM(principal_amount),0) AS total_principal FROM request_deposits")
        total_deposits = cur.fetchone()['total_principal']
 
        # 💰 Total Funded Amount (Approved Loans)
        cur.execute("SELECT COALESCE(SUM(loan_amount),0) AS total_funded FROM loan_requests WHERE status = 'approved'")
        total_funded = cur.fetchone()['total_funded']
 
        cur.close()
 
        return render_template(
            'managerdashboard.html',
            user=user,
            total_customers=total_customers,
            total_pending=total_pending,
            total_deposits=total_deposits,
            total_funded=total_funded
        )
 
        return render_template('managerdashboard.html', user=user, total_customers=total_customers)
   
    return render_template(templates.get(role, 'login.html'), user=user)
 

#Manager Dasboard Routes

@app.route('/manageaccounts')
def manageaccounts():
    return render_template('manageaccounts.html')

@app.route('/manprofile')
def manprofile():
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('manprofile.html',user=user)

@app.route('/manupdate_profile', methods=['GET', 'POST'])
def manupdate_profile():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # GET → load edit form
    if request.method == 'GET':
        cur.execute("""
            SELECT user_id, name, email, mobile,
                   COALESCE(address,'') AS address,
                   COALESCE(city,'')    AS city,
                   COALESCE(state,'')   AS state,
                   COALESCE(country,'') AS country
            FROM bank_users
            WHERE email=%s
        """, (email,))
        user = cur.fetchone()
        cur.close()
        return render_template('manupdateprofile.html', user=user)
 
    # POST → save changes
    cur.execute("""
        SELECT mobile, address, city, state, country, password
        FROM bank_users
        WHERE email=%s
    """, (email,))
    current = cur.fetchone()
 
    mobile   = (request.form.get('mobile')   or '').strip()
    address  = (request.form.get('address')  or '').strip()
    city     = (request.form.get('city')     or '').strip()
    state    = (request.form.get('state')    or '').strip()
    country  = (request.form.get('country')  or '').strip()
 
    curr_pw  = (request.form.get('current_password') or '').strip()
    new_pw   = (request.form.get('new_password')     or '').strip()
    conf_pw  = (request.form.get('confirm_password') or '').strip()
 
    updates = {}
 
    # Only update changed & non-empty values
    if mobile and mobile != (current['mobile'] or ''):
        if not (len(mobile) == 10 and mobile.isdigit()):
            flash('Mobile must be exactly 10 digits.', 'danger')
            cur.close()
            return redirect(url_for('tlupdate_profile'))
        updates['mobile'] = mobile
    if address and address != (current['address'] or ''):
        updates['address'] = address
    if city and city != (current['city'] or ''):
        updates['city'] = city
    if state and state != (current['state'] or ''):
        updates['state'] = state
    if country and country != (current['country'] or ''):
        updates['country'] = country
 
    # Optional password change
    if curr_pw or new_pw or conf_pw:
        if not current or current['password'] != curr_pw:
            flash('Current password is incorrect.', 'danger')
            cur.close()
            return redirect(url_for('manupdate_profile'))
        if not new_pw or new_pw != conf_pw or len(new_pw) < 8:
            flash('New password mismatch or too short (min 8).', 'danger')
            cur.close()
            return redirect(url_for('manupdate_profile'))
        updates['password'] = new_pw
 
    # Helper: human list join
    def human_join(items):
        if not items:
            return ''
        if len(items) == 1:
            return items[0]
        return ', '.join(items[:-1]) + ' and ' + items[-1]
 
    labels = {
        'mobile': 'mobile number',
        'address': 'address',
        'city': 'city',
        'state': 'state',
        'country': 'country',
        'password': 'password'
    }
 
    try:
        if updates:
            set_clause = ", ".join([f"{k}=%s" for k in updates.keys()])
            params = list(updates.values()) + [email]
            cur.execute(f"UPDATE bank_users SET {set_clause} WHERE email=%s", params)
            mysql.connection.commit()
 
            changed = [labels[k] for k in updates.keys()]
            msg = f"Updated {human_join(changed)}."
            # Make password updates feel more “done”
            if 'password' in updates and len(updates) == 1:
                msg = "Password changed successfully."
            flash(msg, 'success')
        else:
            flash('No changes to update.', 'info')
 
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Couldn't save your changes. Error: {e}", 'danger')
    finally:
        cur.close()
 
    return redirect(url_for('manprofile'))



@app.route('/managerapprovals')
def managerapprovals():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('managerapprove.html',user=user)

@app.route('/manage_accounts')
def manage_accounts():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM accounts_requests WHERE status_flag IS NULL")
    requests = cur.fetchall()
    cur.close()
    return render_template("manage-accounts.html", requests=requests,user=user)
 
 
@app.route('/update_request/<request_id>/<action>', methods=['POST'])
def update_request(request_id, action):
    status_flag = "A" if action == "approve" else "R"
    date_now = datetime.now()
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # Update accounts_requests
    cur.execute("""
        UPDATE accounts_requests
        SET status_flag=%s, date_of_action=%s
        WHERE request_id=%s
    """, (status_flag, date_now, request_id))
 
    # Also update accounts (by matching account_number)
    cur.execute("""
        UPDATE saving_accounts a
        JOIN accounts_requests ar ON a.account_number = ar.account_number
        SET a.status_flag=%s, a.date_of_action=%s
        WHERE ar.request_id=%s
    """, (status_flag, date_now, request_id))
 
    # Also update accounts (by matching account_number)
    cur.execute("""
        UPDATE current_accounts a
        JOIN accounts_requests ar ON a.account_number = ar.account_number
        SET a.status_flag=%s, a.date_of_action=%s
        WHERE ar.request_id=%s
    """, (status_flag, date_now, request_id))
 
    # Also update accounts (by matching account_number)
    cur.execute("""
        UPDATE salary_accounts a
        JOIN accounts_requests ar ON a.account_number = ar.account_number
        SET a.status_flag=%s, a.date_of_action=%s
        WHERE ar.request_id=%s
    """, (status_flag, date_now, request_id))
 
    # Also update accounts (by matching account_number)
    cur.execute("""
        UPDATE pmjdy_accounts a
        JOIN accounts_requests ar ON a.account_number = ar.account_number
        SET a.status_flag=%s, a.date_of_action=%s
        WHERE ar.request_id=%s
    """, (status_flag, date_now, request_id))
 
    # Also update accounts (by matching account_number)
    cur.execute("""
        UPDATE pension_accounts a
        JOIN accounts_requests ar ON a.account_number = ar.account_number
        SET a.status_flag=%s, a.date_of_action=%s
        WHERE ar.request_id=%s
    """, (status_flag, date_now, request_id))
 
    # Also update accounts (by matching account_number)
    cur.execute("""
        UPDATE safecustody_accounts a
        JOIN accounts_requests ar ON a.account_number = ar.account_number
        SET a.status_flag=%s, a.date_of_action=%s
        WHERE ar.request_id=%s
    """, (status_flag, date_now, request_id))
 
    mysql.connection.commit()
    cur.close()
 
    return redirect(url_for('manage_accounts'))
 

@app.route('/manview_deposits')
def manview_deposits():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT request_id, deposit_type, account_number,
               first_name, COALESCE(middle_name, '') AS middle_name,
               last_name, email, mobile,
               principal_amount, monthly_installment,
               interest_rate, compounding, tenure_months,
               maturity_amount, created_at, status_flag
        FROM request_deposits
        WHERE status_flag IS NULL OR status_flag = 'A'
        ORDER BY created_at DESC
    """)
    deposits = cur.fetchall()
    cur.close()
    return render_template('manviewdeposits.html', deposits=deposits,user=user)
 
 
@app.route('/update_deposit_request/<request_id>/<action>', methods=['POST'])
def update_deposit_request(request_id, action):
    status_flag = "A" if action == "approve" else "R"
    date_now = datetime.now()
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # 1) Update request_deposits
    cur.execute("""
        UPDATE request_deposits
        SET status_flag=%s, date_of_action=%s
        WHERE request_id=%s
    """, (status_flag, date_now, request_id))
 
    # 2) Update the corresponding deposit row (join by account_number)
    #    We don't know the exact table; pick by deposit_type -> table name.
    cur.execute("""
        SELECT deposit_type, account_number
        FROM request_deposits
        WHERE request_id=%s
    """, (request_id,))
    req = cur.fetchone()
 
    if req:
        dep_type = req['deposit_type']
        table_name = DEPOSIT_TABLES.get(dep_type)
        if table_name:
            # set same status & date in the specific deposit table
            cur.execute(f"""
                UPDATE {table_name}
                SET status_flag=%s, date_of_action=%s
                WHERE account_number=%s
            """, (status_flag, date_now, req['account_number']))
 
    mysql.connection.commit()
    cur.close()
 
    # After action, manager list should no longer show this item (we list only pending)
    return redirect(url_for('manview_deposits'))
 

@app.route('/manage_loans')
def manage_loans():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM loan_requests")
    loans = cur.fetchall()
    return render_template('manage-loans.html', loans=loans,user=user)



@app.route('/viewcards')
def viewcards():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()


    email = session.get('user_email')
    if not email:
        flash("Please login first", "danger")
        return redirect(url_for("login"))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # ✅ Only fetch pending requests
    cur.execute("""
        SELECT r.request_id, r.customer_name, r.customer_email, r.card_type, r.card_subtype,
               r.card_type, r.application_ref, r.created_at, r.status_flag,
               a.id AS app_id
        FROM card_requests r
        LEFT JOIN card_applications a
          ON r.application_ref = a.application_ref
        WHERE r.status_flag IS NULL
        ORDER BY r.created_at DESC
    """)
    requests = cur.fetchall()
    cur.close()
 
    return render_template("view-cards.html", requests=requests, user=user)
 
@app.route('/card_request/<request_id>/<action>', methods=['POST'])
def card_request(request_id, action):
    status_flag = "A" if action == "approve" else "R"
    date_now = datetime.now()
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # Update card_requests
    cur.execute("""
        UPDATE card_requests
        SET status_flag=%s, date_of_action=%s
        WHERE request_id=%s
    """, (status_flag, date_now, request_id))
 
    # Also update applicatios (by matching card_number)
    cur.execute("""
        UPDATE card_applications a
        JOIN card_requests ar ON a.application_ref = ar.application_ref
        SET a.status_flag=%s, a.manager_approval_date=%s
        WHERE ar.request_id=%s
    """, (status_flag, date_now, request_id))
 
    mysql.connection.commit()
    cur.close()
 
    return redirect(url_for('viewcards'))
 

@app.route('/view_cards')
def view_cards():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    # get user for header + user_id for filtering
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE email=%s", (email,))
    user = cur.fetchone()
    if not user:
        cur.close()
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
 
    user_id = user['user_id']
 
    # Fetch this user's card applications
    cur.execute("""
        SELECT application_ref, card_type, card_subtype, status_flag,
               card_number, cvv, issue_limit, limit_utilized,
               requested_for_account_number, created_at, updated_at
        FROM card_applications
        WHERE customer_user_id=%s OR submitted_by_user_id=%s
        ORDER BY created_at DESC, id DESC
    """, (user_id, user_id))
    rows = cur.fetchall()
    cur.close()
 
    # Mapping for UI
    type_label = {
        'credit': 'Credit Card',
        'debit': 'Debit Card',
        'prepaid': 'Prepaid Card'
    }
    status_label = {
        None: 'Pending',   # NULL in DB
        '': 'Pending',     # empty string safeguard
        'A': 'Approved',
        'R': 'Rejected',
        'issued': 'Issued'
    }
 
    def fmt_card_no(n):
        if not n:
            return '—'
        s = ''.join(ch for ch in n if ch.isdigit())
        if not s:
            return n
        return ' '.join(s[i:i+4] for i in range(0, len(s), 4))
 
    cards = []
    for r in rows:
        flag = r.get('status_flag')
        label = status_label.get(flag, 'Pending')  # fallback to Pending
        cards.append({
            'application_ref': r.get('application_ref') or '—',
            'card_type': r.get('card_type') or '',
            'card_type_label': type_label.get((r.get('card_type') or '').lower(), r.get('card_type') or ''),
            'card_subtype': (r.get('card_subtype') or '').upper(),
            'status': flag,
            'status_label': label,
            'card_number': r.get('card_number'),
            'card_number_fmt': fmt_card_no(r.get('card_number')),
            'cvv': r.get('cvv') or '—',
            'issue_limit': r.get('issue_limit') if r.get('issue_limit') is not None else 0,
            'limit_utilized': r.get('limit_utilized') if r.get('limit_utilized') is not None else 0,
            'requested_for_account_number': r.get('requested_for_account_number') or '—',
            'created_at': r.get('created_at'),
            'updated_at': r.get('updated_at'),
        })
 
    return render_template('viewcards.html', user=user, cards=cards)
 

@app.route('/transactions_review')
def transactions_review():
    return render_template('transactions-review.html')

@app.route('/manreport')
def manreport():
    return render_template('manreports.html')

@app.route('/manstaff')
def manstaff():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bank_users WHERE role IN (%s, %s, %s, %s)", ("tl", "Loan_Agent", "Card_Agent", "Investment_Agent"))
    users = cur.fetchall()
    user_list = []
    for u in users:
        user_list.append({
            'user_id': u[0],
            'name': u[1],
            'pan': u[2],
            'aadhaar': u[3],
            'dob': u[4],
            'mobile': u[5],
            'email': u[6],
            'gender': u[7],
            'address': u[8],
            'city': u[9],
            'state': u[10],
            'country': u[11],
            'department': u[12],
            'onboarding_date': u[13],
            'status': u[14],
            'role': u[15],
            'password': u[16],
            'deleted_date': u[17]
        })
 
 
  # ===== Stats =====
    # Total staff count
    cur.execute(
        "SELECT COUNT(*) FROM bank_users WHERE role IN (%s, %s, %s, %s)",
        ("tl", "Loan_Agent", "Card_Agent", "Investment_Agent")
    )
    total_staff = cur.fetchone()[0]
 
    # Active staff today (status = 'Active')
    cur.execute(
        "SELECT COUNT(*) FROM bank_users WHERE status = %s AND role IN (%s, %s, %s, %s)",
        ("Active", "tl", "Loan_Agent", "Card_Agent", "Investment_Agent")
    )
    active_today = cur.fetchone()[0]
 
    # New this month
    cur.execute("""
        SELECT COUNT(*) FROM bank_users
        WHERE MONTH(onboarding_date) = MONTH(CURDATE())
          AND YEAR(onboarding_date) = YEAR(CURDATE())
          AND role IN (%s, %s, %s, %s)
    """, ("tl", "Loan_Agent", "Card_Agent", "Investment_Agent"))
    new_this_month = cur.fetchone()[0]
 
    return render_template(
        'staff-management.html',
        staff=user_list,
        total_staff=total_staff,
        active_today=active_today,
        new_this_month=new_this_month,user=user
    )
 
    
 
 
# Fetch single staff details (AJAX)
@app.route('/staff-details/<user_id>')
def staff_details(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    u = cur.fetchone()
    if u:
        user_data = {
            'user_id': u[0],
            'name': u[1],
            'pan': u[2],
            'aadhaar': u[3],
            'dob': u[4],
            'mobile': u[5],
            'email': u[6],
            'gender': u[7],
            'address': u[8],
            'city': u[9],
            'state': u[10],
            'country': u[11],
            'department': u[12],
            'onboarding_date': u[13],
            'status': u[14],
            'role': u[15],
            'password': u[16],
            'deleted_date': u[17]
        }
        return jsonify(user_data)
    return jsonify({'error': 'Staff not found'}), 404
 
 
# Add new staff
@app.route('/add-staff', methods=['POST'])
def add_staff():
    data = request.form
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO bank_users (user_id, name, role, department, status, last_active, email, mobile, dob, city, state, country, address)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
    """, (
        data['user_id'], data['name'], data['role'], data['department'], data['status'],
        data['email'], data['mobile'], data['dob'], data['city'], data['state'], data['country'], data['address']
    ))
    mysql.connection.commit()
    flash('Staff added successfully!', 'success')
    return redirect(url_for('staff_management'))
 
# Edit staff
@app.route('/edit-staff/<user_id>', methods=['POST'])
def edit_staff(user_id):
    data = request.form
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE bank_users SET name=%s, role=%s, department=%s, status=%s, email=%s, mobile=%s, dob=%s, city=%s, state=%s, country=%s, address=%s
        WHERE user_id=%s
    """, (
        data['name'], data['role'], data['department'], data['status'], data['email'], data['mobile'],
        data['dob'], data['city'], data['state'], data['country'], data['address'], user_id
    ))
    mysql.connection.commit()
    flash('Staff updated successfully!', 'success')
    return redirect(url_for('staff_management'))
 
# Delete staff
@app.route('/delete-staff/<user_id>', methods=['POST'])
def delete_staff(user_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM bank_users WHERE user_id=%s", (user_id,))
    mysql.connection.commit()
    flash('Staff deleted successfully!', 'success')
    return redirect(url_for('staff_management'))
 
 
 
 
# Edit staff

@app.route('/agent_searchprofile', methods=['GET'])
def agent_searchprofile():
    query = request.args.get('query', '').strip()
    search_by = request.args.get('search_by', 'name')  # default to name
 
    if not query:
        flash("Please enter a search term.")
        return redirect(url_for('dashboard'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
# Restrict search only to TL and Loan_Agent roles
    if search_by == "user_id":
        sql = """
            SELECT * FROM bank_users
            WHERE user_id LIKE %s AND role IN (%s, %s, %s, %s)
        """
    else:  # default search by name
        sql = """
            SELECT * FROM bank_users
            WHERE name LIKE %s AND role IN (%s, %s, %s, %s)
        """
 
    like_query = f"%{query}%"
    cur.execute(sql, (like_query, "tl", "Loan_Agent", "Card_Agent", "Investment_Agent"))
    user = cur.fetchone()
    cur.close()
 
    if not user:
        flash("No user found.")
        return redirect(url_for('dashboard'))
 
    return render_template('agentprofile.html', user=user)

@app.route('/api/agent_suggestions')
def agent_suggestions():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Only fetch TL and Loan_Agent
    sql = """
        SELECT user_id, name
        FROM bank_users
        WHERE (name LIKE %s OR user_id LIKE %s)
          AND role IN (%s, %s, %s, %s)
        LIMIT 10
    """
    like_q = f"%{q}%"
    cur.execute(sql, (like_q, like_q, "tl", "Loan_Agent", "Card_Agent", "Investment_Agent"))
    rows = cur.fetchall()
    cur.close()
 
    return jsonify(rows)
 
 

 

@app.route('/branchperformance')
def branchperformance():
    return render_template('branch-performance.html')


# TL Dashboard Routes


def generate_tluser_id(department):
    prefixes = {
        "Cards": "CA",
        "Loans": "LN",
        "Investment": "IV",
        "Forex": "FX",
        

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
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT user_id, name, department, onboarding_date
        FROM agents
        WHERE status='active' AND department='Cards'
    """)
    agents = cur.fetchall()
    return render_template("tlcards.html", agents=agents,user=user)

 # Add User Page
@app.route('/tladduser', methods=['GET', 'POST'])
def tladduser():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()


    if request.method == 'POST':
        data = request.form
        plain_pw = data['password']
        user_id = generate_tluser_id(data['department'])
 
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
 
    return render_template("tladduser.html",user=user)


@app.route('/download_excel')
def download_excel():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM agents")
    members = cur.fetchall()

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Agent Details"

    sheet.append([
        "ID", "Agent Id", "Name", "Dob", "Gender", "Pan Card",
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
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()

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
 
    return render_template("tldeleteuser.html", agents=agents,user=user)


@app.route('/tlprofile')
def tlprofile():
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template("tlprofile.html",user=user)

@app.route('/tlupdate_profile', methods=['GET', 'POST'])
def tlupdate_profile():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # GET → load edit form
    if request.method == 'GET':
        cur.execute("""
            SELECT user_id, name, email, mobile,
                   COALESCE(address,'') AS address,
                   COALESCE(city,'')    AS city,
                   COALESCE(state,'')   AS state,
                   COALESCE(country,'') AS country
            FROM bank_users
            WHERE email=%s
        """, (email,))
        user = cur.fetchone()
        cur.close()
        return render_template('tlupdateprofile.html', user=user)
 
    # POST → save changes
    cur.execute("""
        SELECT mobile, address, city, state, country, password
        FROM bank_users
        WHERE email=%s
    """, (email,))
    current = cur.fetchone()
 
    mobile   = (request.form.get('mobile')   or '').strip()
    address  = (request.form.get('address')  or '').strip()
    city     = (request.form.get('city')     or '').strip()
    state    = (request.form.get('state')    or '').strip()
    country  = (request.form.get('country')  or '').strip()
 
    curr_pw  = (request.form.get('current_password') or '').strip()
    new_pw   = (request.form.get('new_password')     or '').strip()
    conf_pw  = (request.form.get('confirm_password') or '').strip()
 
    updates = {}
 
    # Only update changed & non-empty values
    if mobile and mobile != (current['mobile'] or ''):
        if not (len(mobile) == 10 and mobile.isdigit()):
            flash('Mobile must be exactly 10 digits.', 'danger')
            cur.close()
            return redirect(url_for('tlupdate_profile'))
        updates['mobile'] = mobile
    if address and address != (current['address'] or ''):
        updates['address'] = address
    if city and city != (current['city'] or ''):
        updates['city'] = city
    if state and state != (current['state'] or ''):
        updates['state'] = state
    if country and country != (current['country'] or ''):
        updates['country'] = country
 
    # Optional password change
    if curr_pw or new_pw or conf_pw:
        if not current or current['password'] != curr_pw:
            flash('Current password is incorrect.', 'danger')
            cur.close()
            return redirect(url_for('tlupdate_profile'))
        if not new_pw or new_pw != conf_pw or len(new_pw) < 8:
            flash('New password mismatch or too short (min 8).', 'danger')
            cur.close()
            return redirect(url_for('tlupdate_profile'))
        updates['password'] = new_pw
 
    # Helper: human list join
    def human_join(items):
        if not items:
            return ''
        if len(items) == 1:
            return items[0]
        return ', '.join(items[:-1]) + ' and ' + items[-1]
 
    labels = {
        'mobile': 'mobile number',
        'address': 'address',
        'city': 'city',
        'state': 'state',
        'country': 'country',
        'password': 'password'
    }
 
    try:
        if updates:
            set_clause = ", ".join([f"{k}=%s" for k in updates.keys()])
            params = list(updates.values()) + [email]
            cur.execute(f"UPDATE bank_users SET {set_clause} WHERE email=%s", params)
            mysql.connection.commit()
 
            changed = [labels[k] for k in updates.keys()]
            msg = f"Updated {human_join(changed)}."
            # Make password updates feel more “done”
            if 'password' in updates and len(updates) == 1:
                msg = "Password changed successfully."
            flash(msg, 'success')
        else:
            flash('No changes to update.', 'info')
 
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Couldn't save your changes. Error: {e}", 'danger')
    finally:
        cur.close()
 
    return redirect(url_for('tlprofile'))

 

   


# Loan Page
@app.route('/tlloan')
def tlloan():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT user_id,name, department, onboarding_date 
        FROM agents 
        WHERE status='active' AND department='Loans'
    """)
    agents = cur.fetchall()
    return render_template("tlloan.html", agents=agents,user=user)

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

def clean_digit_str(s):
    return ''.join(ch for ch in (s or '') if ch.isdigit())

def generate_cvv() -> str:
    """3-digit CVV."""
    return f"{random.randint(0, 999):03d}"

def generate_network_card_number(network: str) -> str:
    """
    Generate a mock 16-digit PAN passing Luhn, unique across card_applications & bank_ccards.
    BIN prefixes (mock):
      - visa:       '4'
      - mastercard: '53'
      - rupay:      '60'
    """
    network = (network or '').lower()
    bin_prefix = {'visa': '4', 'mastercard': '53', 'rupay': '60'}.get(network, '60')
    length = 16
 
    cur = mysql.connection.cursor()
    try:
        while True:
            body_len = length - 1 - len(bin_prefix)
            body = ''.join(random.choice(string.digits) for _ in range(body_len))
            partial = bin_prefix + body
            check = _luhn_check_digit(partial)
            card_number = partial + check
 
            # Uniqueness check across both tables
            cur.execute("SELECT 1 FROM card_applications WHERE card_number=%s", (card_number,))
            if cur.fetchone():
                continue
            cur.execute("SELECT 1 FROM bank_ccards WHERE card_number=%s", (card_number,))
            if cur.fetchone():
                continue
            return card_number
    finally:
        cur.close()

def generate_card_request_id():
    """
    Generate unique CR + 3 digit request id
    """
    cur = mysql.connection.cursor()
    while True:
        rid = "CR" + f"{random.randint(0, 999):03d}"
        cur.execute("SELECT 1 FROM card_requests WHERE request_id=%s", (rid,))
        if not cur.fetchone():
            break
    cur.close()
    return rid

def compute_issue_limit_from_cibil(cibil: int | None) -> Decimal:
    """Simple slab logic. Update as you like."""
    if cibil is None:
        return Decimal('0')
    if cibil < 550:
        return Decimal('0')
    if cibil < 650:
        return Decimal('20000')
    if cibil < 700:
        return Decimal('50000')
    if cibil < 750:
        return Decimal('100000')
    return Decimal('200000')

ALLOWED_CARD_TYPES     = {'credit', 'debit', 'prepaid','forex'}
ALLOWED_CARD_NETWORKS  = {'visa', 'mastercard', 'rupay'}
ALLOWED_EMPLOYMENT     = {'salaried','self_employed','student','retired','other'}
def _luhn_check_digit(number_without_check: str) -> str:
    """Return the Luhn check digit for the provided numeric string (no check digit yet)."""
    s = 0
    reverse_digits = number_without_check[::-1]
    for i, ch in enumerate(reverse_digits, start=1):
        d = ord(ch) - 48  # faster int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return str((10 - (s % 10)) % 10)
 
 
 
@app.route('/agentprofile')
def agentprofile():
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template("agentprofile.html",user=user)

@app.route('/agentupdate_profile', methods=['GET', 'POST'])
def agentupdate_profile():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # GET → load edit form
    if request.method == 'GET':
        cur.execute("""
            SELECT user_id, name, email, mobile,
                   COALESCE(address,'') AS address,
                   COALESCE(city,'')    AS city,
                   COALESCE(state,'')   AS state,
                   COALESCE(country,'') AS country
            FROM bank_users
            WHERE email=%s
        """, (email,))
        user = cur.fetchone()
        cur.close()
        return render_template('agentupdateprofile.html', user=user)
 
    # POST → save changes
    cur.execute("""
        SELECT mobile, address, city, state, country, password
        FROM bank_users
        WHERE email=%s
    """, (email,))
    current = cur.fetchone()
 
    mobile   = (request.form.get('mobile')   or '').strip()
    address  = (request.form.get('address')  or '').strip()
    city     = (request.form.get('city')     or '').strip()
    state    = (request.form.get('state')    or '').strip()
    country  = (request.form.get('country')  or '').strip()
 
    curr_pw  = (request.form.get('current_password') or '').strip()
    new_pw   = (request.form.get('new_password')     or '').strip()
    conf_pw  = (request.form.get('confirm_password') or '').strip()
 
    updates = {}
 
    # Only update changed & non-empty values
    if mobile and mobile != (current['mobile'] or ''):
        if not (len(mobile) == 10 and mobile.isdigit()):
            flash('Mobile must be exactly 10 digits.', 'danger')
            cur.close()
            return redirect(url_for('tlupdate_profile'))
        updates['mobile'] = mobile
    if address and address != (current['address'] or ''):
        updates['address'] = address
    if city and city != (current['city'] or ''):
        updates['city'] = city
    if state and state != (current['state'] or ''):
        updates['state'] = state
    if country and country != (current['country'] or ''):
        updates['country'] = country
 
    # Optional password change
    if curr_pw or new_pw or conf_pw:
        if not current or current['password'] != curr_pw:
            flash('Current password is incorrect.', 'danger')
            cur.close()
            return redirect(url_for('agentupdate_profile'))
        if not new_pw or new_pw != conf_pw or len(new_pw) < 8:
            flash('New password mismatch or too short (min 8).', 'danger')
            cur.close()
            return redirect(url_for('agentupdate_profile'))
        updates['password'] = new_pw
 
    # Helper: human list join
    def human_join(items):
        if not items:
            return ''
        if len(items) == 1:
            return items[0]
        return ', '.join(items[:-1]) + ' and ' + items[-1]
 
    labels = {
        'mobile': 'mobile number',
        'address': 'address',
        'city': 'city',
        'state': 'state',
        'country': 'country',
        'password': 'password'
    }
 
    try:
        if updates:
            set_clause = ", ".join([f"{k}=%s" for k in updates.keys()])
            params = list(updates.values()) + [email]
            cur.execute(f"UPDATE bank_users SET {set_clause} WHERE email=%s", params)
            mysql.connection.commit()
 
            changed = [labels[k] for k in updates.keys()]
            msg = f"Updated {human_join(changed)}."
            # Make password updates feel more “done”
            if 'password' in updates and len(updates) == 1:
                msg = "Password changed successfully."
            flash(msg, 'success')
        else:
            flash('No changes to update.', 'info')
 
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Couldn't save your changes. Error: {e}", 'danger')
    finally:
        cur.close()
 
    return redirect(url_for('agentprofile'))


# @app.route('/tlprofile')
# def tlprofile():
#     user_id = session.get('user_id')
    
#     cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
#     user = cur.fetchone()
#     cur.close()
#     return render_template("tlprofile.html",user=user)
 
 


@app.route('/open_cards', methods=['GET', 'POST'])
def open_cards():
    """
    USER flow:
    - Credit: account optional
    - Debit/Prepaid/Forex: account required (must belong to user)
    - Derive issue_limit from CIBIL for credit; 0 otherwise
    - Generate card_number + cvv
    - Insert into both card_applications & card_requests
    - After INSERT, set application_ref like APPYYYYMMDD-000123
    """
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE email=%s", (email,))
    user = cur.fetchone()
    if not user:
        cur.close()
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        preset = (request.args.get('preset') or '').lower()  # can be forex
        my_accounts = get_accounts_for_email(email)
        cur.close()
        return render_template('usercardform.html',
                               user=user,
                               preset=preset,
                               my_accounts=my_accounts)
 
    # POST
    first_name       = (request.form.get('first_name') or '').strip()
    middle_name      = (request.form.get('middle_name') or '').strip()
    last_name        = (request.form.get('last_name') or '').strip()
    applicant_email  = (request.form.get('email') or '').strip()
    applicant_mobile = clean_digit_str(request.form.get('mobile'))
    applicant_aadhaar= clean_digit_str(request.form.get('Addhar'))
    card_type        = (request.form.get('card_type') or '').strip().lower()
    card_subtype     = (request.form.get('card_subtype') or '').strip().lower()
    req_acct         = (request.form.get('requested_for_account_number') or '').strip() or None
 
    cibil_score_str     = (request.form.get('cibil_score') or '').strip()
    monthly_income_str  = (request.form.get('monthly_income') or '').strip()
    employment_type     = (request.form.get('employment_type') or '').strip().lower() or None
 
    if not (first_name and last_name and applicant_email and applicant_mobile and applicant_aadhaar):
        flash('Please fill all required fields.', 'danger')
        return redirect(url_for('open_cards'))
 
    if card_type not in ALLOWED_CARD_TYPES:
        flash('Invalid card type selected.', 'danger')
        return redirect(url_for('open_cards'))
    if card_subtype not in ALLOWED_CARD_NETWORKS:
        flash('Invalid card network selected.', 'danger')
        return redirect(url_for('open_cards'))
 
    # Account requirement (include forex)
    if card_type in ('debit', 'prepaid', 'forex'):
        if not req_acct:
            flash('Please select the account for which you are applying the card.', 'danger')
            return redirect(url_for('open_cards'))
        my_accts = set(get_account_numbers_for_email(email))
        if req_acct not in my_accts:
            flash('Selected account does not belong to you.', 'danger')
            return redirect(url_for('open_cards'))
        try:
            if not sync_account_to_registry(req_acct):
                flash('Selected account was not found in the system.', 'danger')
                return redirect(url_for('open_cards'))
        except Exception as e:
            flash(f'Could not register account for application: {e}', 'danger')
            return redirect(url_for('open_cards'))
    else:
        # credit: optional account
        if req_acct:
            my_accts = set(get_account_numbers_for_email(email))
            if req_acct not in my_accts:
                flash('Selected account does not belong to you.', 'danger')
                return redirect(url_for('open_cards'))
            try:
                if not sync_account_to_registry(req_acct):
                    flash('Selected account was not found in the system.', 'danger')
                    return redirect(url_for('open_cards'))
            except Exception as e:
                flash(f'Could not register account for application: {e}', 'danger')
                return redirect(url_for('open_cards'))
 
    # Credit specifics
    cibil_score = None
    monthly_income = None
    issue_limit = Decimal('0')
    if card_type == 'credit':
        try:
            cibil_score = int(cibil_score_str)
            if cibil_score < 300 or cibil_score > 900:
                raise ValueError()
        except Exception:
            flash('CIBIL score must be an integer between 300 and 900.', 'danger')
            return redirect(url_for('open_cards'))
        if monthly_income_str:
            try:
                monthly_income = int(clean_digit_str(monthly_income_str))
            except Exception:
                monthly_income = None
        issue_limit = compute_issue_limit_from_cibil(cibil_score)
    else:
        employment_type = None  # not stored for non-credit
 
    full_name = ' '.join([p for p in [first_name, middle_name, last_name] if p]).strip()
    applicant_pan = user.get('pan')
 
    # Generate card number & CVV
    gen_card_number = generate_network_card_number(card_subtype)
    gen_cvv         = generate_cvv()
 
    try:
        mysql.connection.begin()
        # Insert into card_applications
        cur.execute("""
            INSERT INTO card_applications
            (customer_user_id, customer_name, customer_email, customer_mobile, customer_aadhaar, customer_pan,
             card_type, card_subtype, requested_for_account_number,
             employment_type, monthly_income, cibil_score,
             submitted_by_role, submitted_by_user_id, submitted_by_agent_id,
             card_number, cvv, issue_limit, limit_utilized)
            VALUES
            (%s,%s,%s,%s,%s,%s,
             %s,%s,%s,
             %s,%s,%s,
             'User', %s, NULL,
             %s, %s, %s, %s)
        """, (
            user['user_id'], full_name, applicant_email, applicant_mobile, applicant_aadhaar, applicant_pan,
            card_type, card_subtype, req_acct,
            employment_type, monthly_income, cibil_score,
            user['user_id'],
            gen_card_number, gen_cvv, str(issue_limit), '0'
        ))
        new_id = cur.lastrowid
        app_ref = f"APP{datetime.now():%Y%m%d}-{new_id:06d}"
        cur.execute("UPDATE card_applications SET application_ref=%s WHERE id=%s", (app_ref, new_id))
 
        # Insert into card_requests
        request_id = generate_card_request_id()
        cur.execute("""
            INSERT INTO card_requests
            (request_id, customer_name, customer_email, customer_mobile, customer_aadhaar, customer_pan,
             card_type, card_subtype, requested_for_account_number,
             employment_type, monthly_income, cibil_score,
             submitted_by_role, submitted_by_user_id, submitted_by_agent_id,
             card_number, cvv, issue_limit, limit_utilized, application_ref)
            VALUES
            (%s,%s,%s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,%s,%s)
        """, (
            request_id, full_name, applicant_email, applicant_mobile, applicant_aadhaar, applicant_pan,
            card_type, card_subtype, req_acct,
            employment_type, monthly_income, cibil_score,
            'User', user['user_id'], None,
            gen_card_number, gen_cvv, str(issue_limit), '0', app_ref
        ))
 
        mysql.connection.commit()
        flash(f'Application submitted. Ref: {app_ref} | Card: {gen_card_number} | CVV: {gen_cvv} | Issue Limit: ₹{issue_limit}', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Could not submit application: {e}', 'danger')
    finally:
        cur.close()
 
    return redirect(url_for('dashboard'))
 
 
@app.route('/cards/agent/apply', methods=['GET', 'POST'])
def agent_apply_card():
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()

    """
    CARD AGENT flow:
    - Credit: account optional; Debit/Prepaid/Forex: account required
    - Derive issue_limit from CIBIL for credit; 0 otherwise
    - Generate card_number + cvv
    - Insert into both card_applications & card_requests
    - After INSERT, set application_ref
    """
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE email=%s", (email,))
    me = cur.fetchone()
    if not me:
        cur.close()
        flash('Agent not found.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        cur.close()
        return render_template('agent_card_form.html', agent=me)
 
    # POST
    applicant_email   = (request.form.get('applicant_email') or '').strip()
    applicant_name    = (request.form.get('customer_name') or '').strip()
    applicant_mobile  = clean_digit_str(request.form.get('mobile'))
    applicant_aadhaar = clean_digit_str(request.form.get('aadharNumber'))
    applicant_pan     = (request.form.get('panNumber') or '').strip()
 
    card_type         = (request.form.get('card_type') or '').strip().lower()
    card_subtype      = (request.form.get('card_subtype') or '').strip().lower()
    req_acct          = (request.form.get('requested_for_account_number') or '').strip() or None
 
    cibil_score_str   = (request.form.get('cibil_score') or '').strip()
    monthly_income_str= (request.form.get('monthly_income') or '').strip()
    employment_type   = (request.form.get('employment_type') or '').strip().lower() or None
 
    if not (applicant_email and applicant_name and applicant_mobile and applicant_aadhaar):
        flash('Please fill all required fields.', 'danger')
        return redirect(url_for('agent_apply_card'))
 
    if card_type not in ALLOWED_CARD_TYPES or card_subtype not in ALLOWED_CARD_NETWORKS:
        flash('Invalid card type/network.', 'danger')
        return redirect(url_for('agent_apply_card'))
 
    # Customer row
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE email=%s", (applicant_email,))
    cust = cur.fetchone()
    if not cust:
        cur.close()
        flash('Customer email not found in the system.', 'danger')
        return redirect(url_for('agent_apply_card'))
 
    # Account requirement (include forex)
    if card_type in ('debit', 'prepaid', 'forex'):
        if not req_acct:
            cur.close()
            flash('Please select the customer account for this application.', 'danger')
            return redirect(url_for('agent_apply_card'))
        cust_accts = set(get_account_numbers_for_email(applicant_email))
        if req_acct not in cust_accts:
            cur.close()
            flash('Selected account does not belong to the customer.', 'danger')
            return redirect(url_for('agent_apply_card'))
        try:
            if not sync_account_to_registry(req_acct):
                cur.close()
                flash('Selected account was not found in the system.', 'danger')
                return redirect(url_for('agent_apply_card'))
        except Exception as e:
            cur.close()
            flash(f'Could not register account for application: {e}', 'danger')
            return redirect(url_for('agent_apply_card'))
    else:
        if req_acct:
            cust_accts = set(get_account_numbers_for_email(applicant_email))
            if req_acct not in cust_accts:
                cur.close()
                flash('Selected account does not belong to the customer.', 'danger')
                return redirect(url_for('agent_apply_card'))
            try:
                if not sync_account_to_registry(req_acct):
                    cur.close()
                    flash('Selected account was not found in the system.', 'danger')
                    return redirect(url_for('agent_apply_card'))
            except Exception as e:
                cur.close()
                flash(f'Could not register account for application: {e}', 'danger')
                return redirect(url_for('agent_apply_card'))
 
    # Credit specifics
    cibil_score = None
    monthly_income = None
    issue_limit = Decimal('0')
    if card_type == 'credit':
        try:
            cibil_score = int(cibil_score_str)
            if cibil_score < 300 or cibil_score > 900:
                raise ValueError()
        except Exception:
            cur.close()
            flash('CIBIL score must be an integer between 300 and 900.', 'danger')
            return redirect(url_for('agent_apply_card'))
        if monthly_income_str:
            try:
                monthly_income = int(clean_digit_str(monthly_income_str))
            except Exception:
                monthly_income = None
        issue_limit = compute_issue_limit_from_cibil(cibil_score)
    else:
        employment_type = None
 
    # Generate card number & CVV
    gen_card_number = generate_network_card_number(card_subtype)
    gen_cvv         = generate_cvv()
 
    try:
        mysql.connection.begin()
        # Insert into card_applications
        cur.execute("""
            INSERT INTO card_applications
            (customer_user_id, customer_name, customer_email, customer_mobile, customer_aadhaar, customer_pan,
             card_type, card_subtype, requested_for_account_number,
             employment_type, monthly_income, cibil_score,
             submitted_by_role, submitted_by_user_id, submitted_by_agent_id,
             card_number, cvv, issue_limit, limit_utilized)
            VALUES
            (%s,%s,%s,%s,%s,%s,
             %s,%s,%s,
             %s,%s,%s,
             'Card_Agent', NULL, %s,
             %s, %s, %s, %s)
        """, (
            cust['user_id'], applicant_name, applicant_email, applicant_mobile, applicant_aadhaar, applicant_pan,
            card_type, card_subtype, req_acct,
            employment_type, monthly_income, cibil_score,
            me['user_id'],
            gen_card_number, gen_cvv, str(issue_limit), '0'
        ))
        new_id = cur.lastrowid
        app_ref = f"APP{datetime.now():%Y%m%d}-{new_id:06d}"
        cur.execute("UPDATE card_applications SET application_ref=%s WHERE id=%s", (app_ref, new_id))
 
        # Insert into card_requests
        request_id = generate_card_request_id()
        cur.execute("""
            INSERT INTO card_requests
            (request_id, customer_name, customer_email, customer_mobile, customer_aadhaar, customer_pan,
            card_type, card_subtype, requested_for_account_number,
            employment_type, monthly_income, cibil_score,
            submitted_by_role, submitted_by_user_id, submitted_by_agent_id,
            card_number, cvv, issue_limit, limit_utilized, application_ref)
            VALUES
            (%s,%s,%s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,%s,%s)
        """, (
            request_id, applicant_name, applicant_email, applicant_mobile, applicant_aadhaar, applicant_pan,
            card_type, card_subtype, req_acct,
            employment_type, monthly_income, cibil_score,
            'Card_Agent', None, me['user_id'],
            gen_card_number, gen_cvv, str(issue_limit), '0', app_ref
        ))
 
        mysql.connection.commit()
        flash(f'Card application submitted. Ref: {app_ref} | Card: {gen_card_number} | CVV: {gen_cvv} | Issue Limit: ₹{issue_limit}', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Could not submit application: {e}', 'danger')
    finally:
        cur.close()
 
    return render_template('cardagent_dashboard.html',user=user)
 
 
 
 

@app.route('/api/user-accounts', methods=['GET'])
def api_user_accounts():
    email = (request.args.get('email') or '').strip()
    if not email:
        return jsonify({"ok": True, "accounts": []})
    try:
        accts = get_accounts_for_email(email)
        data = [{"account_number": a["account_number"], "account_type": a["account_type"]} for a in accts]
        return jsonify({"ok": True, "accounts": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
 
 
def sync_account_to_registry(account_number: str) -> bool:
    """
    Ensure the account exists in accounts_registry (for FK).
    Uses find_account_by_number() to discover table, type, owner.
    """
    info = find_account_by_number(account_number, for_update=False)
    if not info:
        return False
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Upsert (use alias style to avoid deprecated VALUES() usage)
        cur.execute("""
            INSERT INTO accounts_registry (account_number, account_type, table_name, owner_user_id)
            VALUES (%s, %s, %s, %s)
            AS ar
            ON DUPLICATE KEY UPDATE
              account_type  = ar.account_type,
              table_name    = ar.table_name,
              owner_user_id = ar.owner_user_id
        """, (info['account_number'], info['account_type'], info['table_name'], info['user_id']))
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
    cur.close()
    return True


 
 

@app.route('/userdebitform')
def userdebitform():
    return render_template('userdebitform.html')

@app.route('/userprepaidform')
def userprepaidform():
    return render_template('userprepaidform.html')


@app.route('/paybill')
def paybill():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('paybill.html',user=user)



@app.route('/banktransfer')
def banktransfer():
    return render_template('banktransfer.html')






#Dashboard - user->loan



@app.route('/userdashloan')
def userdashloan():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('userloand.html',user=user)
 
@app.route('/userpersonalloan')
def userpersonalloan():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('userpersonalloan.html',user=user)
 
@app.route('/userbusinessloan')
def userbusinessloan():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    
    return render_template('userbusinessloan.html',user=user)

#Loan Agent Dashboard
 
 
import os, uuid, re, MySQLdb
from datetime import datetime
from decimal import Decimal
from werkzeug.utils import secure_filename
from flask import request, render_template, redirect, url_for, session, flash, jsonify
 
# ---- uploads ----
app.config.setdefault('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
 
 
# ---------- helpers ----------
def _status_label(s):
    return {
        'pending_manager': 'Pending',
        'approved': 'Approved',
        'rejected': 'Rejected',
        'issued': 'Issued'
    }.get((s or '').lower(), s or '—')
 
 
def save_upload(file_storage, subdir='signatures'):
    """Save uploaded file and return relative path under UPLOAD_FOLDER."""
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return None
    folder = os.path.join(app.config['UPLOAD_FOLDER'], subdir)
    os.makedirs(folder, exist_ok=True)
    fname = secure_filename(file_storage.filename) or 'upload'
    root, ext = os.path.splitext(fname)
    new_name = f"{root}_{uuid.uuid4().hex[:8]}{ext or '.png'}"
    full_path = os.path.join(folder, new_name)
    file_storage.save(full_path)
    rel = os.path.relpath(full_path, app.config['UPLOAD_FOLDER'])
    return rel.replace('\\', '/')
 
 
def compute_emi(principal, annual_rate_percent, tenure_years):
    """
    EMI = P * r * (1+r)^n / ((1+r)^n - 1) ; r = annual/12/100 ; n = years*12
    """
    try:
        P = float(principal)
        r = float(annual_rate_percent) / 12.0 / 100.0
        n = int(tenure_years) * 12
        if P <= 0 or n <= 0:
            return 0.0
        if r == 0:
            return round(P / n, 2)
        emi = P * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
        return round(emi, 2)
    except Exception:
        return 0.0
 
 
def find_interest_rate(category, interest_type, amount, tenure_years):
    """
    Look up interest rate from loan_interest_rate_matrix; return float or None.
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cur.execute("""
            SELECT rate_percent
            FROM loan_interest_rate_matrix
            WHERE loan_category = %s
              AND interest_type = %s
              AND is_active = 1
              AND (effective_from <= CURDATE())
              AND (effective_to IS NULL OR effective_to >= CURDATE())
              AND %s BETWEEN min_amount AND max_amount
              AND %s BETWEEN min_tenure_years AND max_tenure_years
            ORDER BY (max_amount - min_amount) ASC,
                     (max_tenure_years - min_tenure_years) ASC, id ASC
            LIMIT 1
        """, (category, interest_type, amount, tenure_years))
        row = cur.fetchone()
        return float(row['rate_percent']) if row else None
    finally:
        cur.close()
 
 
def _current_user():
    """
    Try session email first, then user_id. Returns bank_users row or None.
    """
    email = session.get('user_email')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if email:
            cur.execute("SELECT * FROM bank_users WHERE email=%s", (email,))
            u = cur.fetchone()
            if u:
                return u
        uid = session.get('user_id')
        if uid:
            cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (uid,))
            return cur.fetchone()
        return None
    finally:
        cur.close()
 
 
def _normalize_role(role_str: str) -> str:
    # "Loan Agent" / "Loan_Agent" / "loan-agent" => "loan_agent"
    return re.sub(r'[^a-z0-9]+', '_', (role_str or '').strip().lower()).strip('_')
 
 
def _user_role(u):
    raw = (u.get('role') or u.get('user_role') or u.get('staff_role') or '')
    return _normalize_role(raw)
 
 
def table_has_column(table_name, column_name):
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s
        """, (table_name, column_name))
        return (cur.fetchone()[0] or 0) > 0
    finally:
        cur.close()
 
 
def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0
 
 
def _compute_interest_rate(kind, interest_type, amount, tenure_years):
    rate = find_interest_rate(
        (kind or '').lower(),
        (interest_type or '').title(),
        _safe_float(amount),
        int(tenure_years or 0)
    )
    if rate is not None:
        return rate
    # defaults
    defaults = {
        ('home', 'Floating'): 8.50,
        ('home', 'Fixed'):    9.00,
        ('personal', 'Fixed'):13.50,
        ('business', 'Fixed'):12.50
    }
    return defaults.get(((kind or '').lower(), (interest_type or '').title()), 12.0)
 
 
def _compute_emi(amount, rate, tenure_years):
    return compute_emi(_safe_float(amount), _safe_float(rate), int(tenure_years or 0))
 
 
def generate_loan_request_id():
    """
    Generate unique LR + 3 digit request id for loans
    """
    cur = mysql.connection.cursor()
    while True:
        rid = "LR" + f"{random.randint(0, 999):03d}"
        cur.execute("SELECT 1 FROM loan_requests WHERE request_id=%s", (rid,))
        if not cur.fetchone():
            break
    cur.close()
    return rid
 
def generate_invest_request_id():
    """
    Generate unique IR + 3 digit request id for investments
    """
    cur = mysql.connection.cursor()
    while True:
        rid = "IR" + f"{random.randint(0, 999):03d}"
        cur.execute("SELECT 1 FROM investment_applications WHERE request_id=%s", (rid,))
        if not cur.fetchone():
            break
    cur.close()
    return rid
 
 
# ---------- live-rate mini API ----------
@app.route('/api/loan-rate')
def api_loan_rate():
    category      = (request.args.get('category') or '').strip().lower()      # 'home'|'personal'|'business'
    interest_type = (request.args.get('interest_type') or '').strip().title() # 'Floating'|'Fixed'
    amount        = float(request.args.get('amount') or 0)
    tenure_years  = int(request.args.get('tenure_years') or 0)
 
    DEFAULTS = {
        ('home', 'Floating'): 8.50,
        ('home', 'Fixed'):    9.00,
        ('personal', 'Fixed'):13.50,
        ('business', 'Fixed'):12.50
    }
    rate = find_interest_rate(category, interest_type, amount, tenure_years)
    if rate is None:
        rate = DEFAULTS.get((category, interest_type), 12.00)
    emi = compute_emi(amount, rate, tenure_years)
    return jsonify({"ok": True, "rate_percent": rate, "emi": emi})
 
 
# ========== USER: HOME LOAN ==========
@app.route('/homeloan', methods=['GET', 'POST'])
def homeloan():
    user = _current_user()
    if not user:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        return render_template('userhomeapply.html', user=user)
 
    f, files = request.form, request.files
    try:
        # Applicant
        applicant_name = (f.get('applicantName') or '').strip()
        dob            = f.get('dob') or None
        age            = f.get('age') or None
        gender         = (f.get('gender') or '').strip()
        address        = (f.get('address') or '').strip()
        pin            = (f.get('pin') or '').strip()
        telephone      = (f.get('telephone') or '').strip()
        mobile         = (f.get('mobile') or '').strip()
        nationality    = (f.get('nationality') or '').strip()
        marital_status = (f.get('maritalStatus') or '').strip()
        pan            = (f.get('pan') or '').strip()
 
        # Employment
        employment_type = (f.get('employmentType') or '').strip()
        company_name    = (f.get('companyName') or '').strip()
        designation     = (f.get('designation') or '').strip()
        gross_income    = Decimal(f.get('grossIncome') or '0')
        experience      = int(f.get('experience') or 0)
        current_exp     = f.get('currentExp')
        current_exp     = int(current_exp) if current_exp else None
 
        # Property
        property_address = (f.get('propertyAddress') or '').strip()
        property_type    = (f.get('propertyType') or '').strip()
        property_age     = f.get('propertyAge')
        property_age     = int(property_age) if property_age else None
        built_up_area    = int(f.get('builtUpArea') or 0)
        property_value   = Decimal(f.get('propertyValue') or '0')
 
        # Loan
        loan_amount      = Decimal(f.get('loanAmount') or '0')
        loan_tenure      = int(f.get('loanTenure') or 0)
        builder_name     = (f.get('builderName') or '').strip()
        purpose          = (f.get('purpose') or '').strip()
        interest_type    = (f.get('interestType') or '').strip().title()
 
        # Financials
        existing_loan    = Decimal(f.get('existingLoan') or '0')
        other_loan       = Decimal(f.get('otherLoan') or '0')
        credit_card      = Decimal(f.get('creditCard') or '0')
        savings          = Decimal(f.get('savings') or '0')
        other_assets     = Decimal(f.get('otherAssets') or '0')
 
        # Bank
        bank_name        = (f.get('bankName') or '').strip()
        account_number   = (f.get('accountNumber') or '').strip()
        account_type     = (f.get('accountType') or '').strip()
        account_years    = int(f.get('accountYears') or 0)
 
        # Co-app
        co_name          = (f.get('coApplicantName') or '').strip()
        co_relation      = (f.get('coApplicantRelation') or '').strip()
        co_income        = f.get('coApplicantIncome')
        co_income        = Decimal(co_income) if co_income else None
 
        # Docs / flags
        has_id_proof     = 1 if f.get('idProof') else 0
        has_addr_proof   = 1 if f.get('addressProof') else 0
        has_income_proof = 1 if f.get('incomeProof') else 0
        has_property_docs= 1 if f.get('propertyDocs') else 0
        declaration      = 1 if f.get('declaration') else 0
 
        # Uploads
        applicant_sig    = save_upload(files.get('applicantSignature'), 'signatures')
        coapp_sig        = save_upload(files.get('coApplicantSignature'), 'signatures')
 
        # Submission
        application_date = f.get('date') or datetime.today().strftime('%Y-%m-%d')
        place            = (f.get('place') or '').strip()
 
        # rate & emi
        rate = find_interest_rate('home', interest_type, float(loan_amount), int(loan_tenure))
        if rate is None:
            rate = 8.50 if interest_type == 'Floating' else 9.00
        emi = compute_emi(loan_amount, rate, loan_tenure)
 
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
       
        request_id = generate_loan_request_id()
 
        cur.execute("""
            INSERT INTO home_loan_applications
            (request_id, user_id, applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
             marital_status, pan, employment_type, company_name, designation, gross_annual_income,
             total_experience_years, current_company_experience_years, property_address, property_type,
             property_age_years, built_up_area_sqft, property_value, loan_amount, loan_tenure_years,
             builder_name, purpose, interest_type, interest_rate, emi_amount,
             existing_home_loan, other_loans, credit_card_limits, savings_investments, other_assets,
             bank_name, bank_account_number, bank_account_type, bank_years_with_bank,
             coapplicant_name, coapplicant_relationship, coapplicant_annual_income,
             has_id_proof, has_address_proof, has_income_proof, has_property_docs, declaration_agreed,
             applicant_signature_path, coapplicant_signature_path, application_date, place, status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,%s,
             %s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,
             %s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,'pending_manager')
        """, (
            request_id, user['user_id'], applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, str(gross_income),
            experience, current_exp, property_address, property_type,
            property_age, built_up_area, str(property_value), str(loan_amount), loan_tenure,
            builder_name, purpose, interest_type, str(rate), str(emi),
            str(existing_loan), str(other_loan), str(credit_card), str(savings), str(other_assets),
            bank_name, account_number, account_type, account_years,
            co_name, co_relation, (str(co_income) if co_income is not None else None),
            has_id_proof, has_addr_proof, has_income_proof, has_property_docs, declaration,
            applicant_sig, coapp_sig, application_date, place
        ))
 
        cur.execute("""
            INSERT INTO loan_requests
            (request_id, loan_type,
            applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, gross_annual_income,
            total_experience_years, current_company_experience_years, property_address, property_type,
            property_age_years, built_up_area_sqft, property_value, loan_amount, loan_tenure_years,
            builder_name, purpose, interest_type, interest_rate, emi_amount,
            existing_home_loan, other_loans, credit_card_limits, savings_investments, other_assets,
            bank_name, bank_account_number, bank_account_type, bank_years_with_bank,
            coapplicant_name, coapplicant_relationship, coapplicant_annual_income,
            has_id_proof, has_address_proof, has_income_proof, has_property_docs, declaration_agreed,
            applicant_signature_path, coapplicant_signature_path, application_date, place, status)
            VALUES
            (%s,'home',
            %s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,'pending_manager')
        """, (
            request_id,
            applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, str(gross_income),
            experience, current_exp, property_address, property_type,
            property_age, built_up_area, str(property_value), str(loan_amount), loan_tenure,
            builder_name, purpose, interest_type, str(rate), str(emi),
            str(existing_loan), str(other_loan), str(credit_card), str(savings), str(other_assets),
            bank_name, account_number, account_type, account_years,
            co_name, co_relation, (str(co_income) if co_income is not None else None),
            has_id_proof, has_addr_proof, has_income_proof, has_property_docs, declaration,
            applicant_sig, coapp_sig, application_date, place
        ))
 
        mysql.connection.commit()
        flash(f'Home loan application submitted. Rate {rate:.2f}% • EMI ₹{emi:.2f}', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Could not submit loan application: {e}', 'danger')
    return redirect(url_for('userdashloan'))
 
 
# ========== USER: PERSONAL LOAN ==========
@app.route('/personal_loan', methods=['GET', 'POST'])
def personal_loan():
    user = _current_user()
    if not user:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        return render_template('Loan_personal.html', user=user)
 
    f, files = request.form, request.files
    try:
        # Common
        applicant_name = (f.get('applicantName') or '').strip()
        dob            = f.get('dob') or None
        age            = f.get('age') or None
        gender         = (f.get('gender') or '').strip()
        address        = (f.get('address') or '').strip()
        pin            = (f.get('pin') or '').strip()
        telephone      = (f.get('telephone') or '').strip()
        mobile         = (f.get('mobile') or '').strip()
        nationality    = (f.get('nationality') or '').strip()
        marital_status = (f.get('maritalStatus') or '').strip()
        pan            = (f.get('pan') or '').strip()
 
        employment_type = (f.get('employmentType') or '').strip()
        company_name    = (f.get('companyName') or '').strip()
        designation     = (f.get('designation') or '').strip()
        gross_income    = Decimal(f.get('grossIncome') or '0')
        experience      = int(f.get('experience') or 0)
        current_exp     = f.get('currentExp')
        current_exp     = int(current_exp) if current_exp else None
 
        # personal: no property
        property_address = ''
        property_type    = ''
        property_age     = None
        built_up_area    = 0
        property_value   = Decimal('0')
 
        loan_amount      = Decimal(f.get('loanAmount') or '0')
        loan_tenure      = int(f.get('loanTenure') or 0)
        builder_name     = ''
        purpose          = (f.get('purpose') or 'personal').strip()
        interest_type    = (f.get('interestType') or '').strip().title()
 
        existing_loan    = Decimal(f.get('existingLoan') or '0')
        other_loan       = Decimal(f.get('otherLoan') or '0')
        credit_card      = Decimal(f.get('creditCard') or '0')
        savings          = Decimal(f.get('savings') or '0')
        other_assets     = Decimal(f.get('otherAssets') or '0')
 
        bank_name        = (f.get('bankName') or '').strip()
        account_number   = (f.get('accountNumber') or '').strip()
        account_type     = (f.get('accountType') or '').strip()
        account_years    = int(f.get('accountYears') or 0)
 
        co_name          = (f.get('coApplicantName') or '').strip()
        co_relation      = (f.get('coApplicantRelation') or '').strip()
        co_income        = f.get('coApplicantIncome')
        co_income        = Decimal(co_income) if co_income else None
 
        has_id_proof     = 1 if f.get('idProof') else 0
        has_addr_proof   = 1 if f.get('addressProof') else 0
        has_income_proof = 1 if f.get('incomeProof') else 0
        has_property_docs= 1 if f.get('propertyDocs') else 0
        declaration      = 1 if f.get('declaration') else 0
 
        applicant_sig    = save_upload(files.get('applicantSignature'), 'signatures')
        coapp_sig        = save_upload(files.get('coApplicantSignature'), 'signatures')
 
        application_date = f.get('date') or datetime.today().strftime('%Y-%m-%d')
        place            = (f.get('place') or '').strip()
 
        rate = find_interest_rate('personal', interest_type, float(loan_amount), int(loan_tenure))
        if rate is None:
            rate = 13.50
        emi  = compute_emi(loan_amount, rate, loan_tenure)
 
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
       
        request_id = generate_loan_request_id()
 
        cur.execute("""
            INSERT INTO personal_loan_applications
            (request_id, user_id, applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
             marital_status, pan, employment_type, company_name, designation, gross_annual_income,
             total_experience_years, current_company_experience_years, property_address, property_type,
             property_age_years, built_up_area_sqft, property_value, loan_amount, loan_tenure_years,
             builder_name, purpose, interest_type, interest_rate, emi_amount,
             existing_home_loan, other_loans, credit_card_limits, savings_investments, other_assets,
             bank_name, bank_account_number, bank_account_type, bank_years_with_bank,
             coapplicant_name, coapplicant_relationship, coapplicant_annual_income,
             has_id_proof, has_address_proof, has_income_proof, has_property_docs, declaration_agreed,
             applicant_signature_path, coapplicant_signature_path, application_date, place, status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,%s,
             %s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,
             %s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,'pending_manager')
        """, (
            request_id, user['user_id'], applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, str(gross_income),
            experience, current_exp, property_address, property_type,
            property_age, built_up_area, str(property_value), str(loan_amount), loan_tenure,
            builder_name, purpose, interest_type, str(rate), str(emi),
            str(existing_loan), str(other_loan), str(credit_card), str(savings), str(other_assets),
            bank_name, account_number, account_type, account_years,
            co_name, co_relation, (str(co_income) if co_income is not None else None),
            has_id_proof, has_addr_proof, has_income_proof, has_property_docs, declaration,
            applicant_sig, coapp_sig, application_date, place
        ))
 
        cur.execute("""
            INSERT INTO loan_requests
            (request_id, loan_type,
            applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, gross_annual_income,
            total_experience_years, current_company_experience_years, property_address, property_type,
            property_age_years, built_up_area_sqft, property_value, loan_amount, loan_tenure_years,
            builder_name, purpose, interest_type, interest_rate, emi_amount,
            existing_home_loan, other_loans, credit_card_limits, savings_investments, other_assets,
            bank_name, bank_account_number, bank_account_type, bank_years_with_bank,
            coapplicant_name, coapplicant_relationship, coapplicant_annual_income,
            has_id_proof, has_address_proof, has_income_proof, has_property_docs, declaration_agreed,
            applicant_signature_path, coapplicant_signature_path, application_date, place, status)
            VALUES
            (%s,'personal',
            %s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,'pending_manager')
        """, (
            request_id,
            applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, str(gross_income),
            experience, current_exp, property_address, property_type,
            property_age, built_up_area, str(property_value), str(loan_amount), loan_tenure,
            builder_name, purpose, interest_type, str(rate), str(emi),
            str(existing_loan), str(other_loan), str(credit_card), str(savings), str(other_assets),
            bank_name, account_number, account_type, account_years,
            co_name, co_relation, (str(co_income) if co_income is not None else None),
            has_id_proof, has_addr_proof, has_income_proof, has_property_docs, declaration,
            applicant_sig, coapp_sig, application_date, place
        ))
 
        mysql.connection.commit()
        flash(f'Personal loan application submitted. Rate {rate:.2f}% • EMI ₹{emi:.2f}', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Could not submit personal loan application: {e}', 'danger')
    return redirect(url_for('userdashloan'))
 
 
# ========== USER: BUSINESS LOAN ==========
@app.route('/Business_loan', methods=['GET', 'POST'])
def Business_loan():
    user = _current_user()
    if not user:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        return render_template('Business_Loan.html', user=user)
 
    f, files = request.form, request.files
    try:
        applicant_name = (f.get('applicantName') or '').strip()
        dob            = f.get('dob') or None
        age            = f.get('age') or None
        gender         = (f.get('gender') or '').strip()
        address        = (f.get('address') or '').strip()
        pin            = (f.get('pin') or '').strip()
        telephone      = (f.get('telephone') or '').strip()
        mobile         = (f.get('mobile') or '').strip()
        nationality    = (f.get('nationality') or '').strip()
        marital_status = (f.get('maritalStatus') or '').strip()
        pan            = (f.get('pan') or '').strip()
 
        employment_type = (f.get('employmentType') or '').strip()
        company_name    = (f.get('companyName') or '').strip()
        designation     = (f.get('designation') or '').strip()
        gross_income    = Decimal(f.get('grossIncome') or '0')
        experience      = int(f.get('experience') or 0)
        current_exp     = f.get('currentExp')
        current_exp     = int(current_exp) if current_exp else None
 
        # business: no property
        property_address = ''
        property_type    = ''
        property_age     = None
        built_up_area    = 0
        property_value   = Decimal('0')
 
        loan_amount      = Decimal(f.get('loanAmount') or '0')
        loan_tenure      = int(f.get('loanTenure') or 0)
        builder_name     = ''
        purpose          = (f.get('purpose') or 'business').strip()
        interest_type    = (f.get('interestType') or '').strip().title()
 
        existing_loan    = Decimal(f.get('existingLoan') or '0')
        other_loan       = Decimal(f.get('otherLoan') or '0')
        credit_card      = Decimal(f.get('creditCard') or '0')
        savings          = Decimal(f.get('savings') or '0')
        other_assets     = Decimal(f.get('otherAssets') or '0')
 
        bank_name        = (f.get('bankName') or '').strip()
        account_number   = (f.get('accountNumber') or '').strip()
        account_type     = (f.get('accountType') or '').strip()
        account_years    = int(f.get('accountYears') or 0)
 
        co_name          = (f.get('coApplicantName') or '').strip()
        co_relation      = (f.get('coApplicantRelation') or '').strip()
        co_income        = f.get('coApplicantIncome')
        co_income        = Decimal(co_income) if co_income else None
 
        has_id_proof     = 1 if f.get('idProof') else 0
        has_addr_proof   = 1 if f.get('addressProof') else 0
        has_income_proof = 1 if f.get('incomeProof') else 0
        has_property_docs= 1 if f.get('propertyDocs') else 0
        declaration      = 1 if f.get('declaration') else 0
 
        applicant_sig    = save_upload(files.get('applicantSignature'), 'signatures')
        coapp_sig        = save_upload(files.get('coApplicantSignature'), 'signatures')
 
        application_date = f.get('date') or datetime.today().strftime('%Y-%m-%d')
        place            = (f.get('place') or '').strip()
 
        rate = find_interest_rate('business', interest_type, float(loan_amount), int(loan_tenure))
        if rate is None:
            rate = 12.50
        emi  = compute_emi(loan_amount, rate, loan_tenure)
 
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
        request_id = generate_loan_request_id()
 
        cur.execute("""
            INSERT INTO business_loan_applications
            (request_id, user_id, applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
             marital_status, pan, employment_type, company_name, designation, gross_annual_income,
             total_experience_years, current_company_experience_years, property_address, property_type,
             property_age_years, built_up_area_sqft, property_value, loan_amount, loan_tenure_years,
             builder_name, purpose, interest_type, interest_rate, emi_amount,
             existing_home_loan, other_loans, credit_card_limits, savings_investments, other_assets,
             bank_name, bank_account_number, bank_account_type, bank_years_with_bank,
             coapplicant_name, coapplicant_relationship, coapplicant_annual_income,
             has_id_proof, has_address_proof, has_income_proof, has_property_docs, declaration_agreed,
             applicant_signature_path, coapplicant_signature_path, application_date, place, status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,%s,
             %s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,
             %s,%s,%s,
             %s,%s,%s,%s,%s,
             %s,%s,%s,%s,'pending_manager')
        """, (
            request_id, user['user_id'], applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, str(gross_income),
            experience, current_exp, property_address, property_type,
            property_age, built_up_area, str(property_value), str(loan_amount), loan_tenure,
            builder_name, purpose, interest_type, str(rate), str(emi),
            str(existing_loan), str(other_loan), str(credit_card), str(savings), str(other_assets),
            bank_name, account_number, account_type, account_years,
            co_name, co_relation, (str(co_income) if co_income is not None else None),
            has_id_proof, has_addr_proof, has_income_proof, has_property_docs, declaration,
            applicant_sig, coapp_sig, application_date, place
        ))
 
 
        cur.execute("""
            INSERT INTO loan_requests
            (request_id, loan_type,
            applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, gross_annual_income,
            total_experience_years, current_company_experience_years, property_address, property_type,
            property_age_years, built_up_area_sqft, property_value, loan_amount, loan_tenure_years,
            builder_name, purpose, interest_type, interest_rate, emi_amount,
            existing_home_loan, other_loans, credit_card_limits, savings_investments, other_assets,
            bank_name, bank_account_number, bank_account_type, bank_years_with_bank,
            coapplicant_name, coapplicant_relationship, coapplicant_annual_income,
            has_id_proof, has_address_proof, has_income_proof, has_property_docs, declaration_agreed,
            applicant_signature_path, coapplicant_signature_path, application_date, place, status)
            VALUES
            (%s,'business',
            %s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,'pending_manager')
        """, (
            request_id,
            applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
            marital_status, pan, employment_type, company_name, designation, str(gross_income),
            experience, current_exp, property_address, property_type,
            property_age, built_up_area, str(property_value), str(loan_amount), loan_tenure,
            builder_name, purpose, interest_type, str(rate), str(emi),
            str(existing_loan), str(other_loan), str(credit_card), str(savings), str(other_assets),
            bank_name, account_number, account_type, account_years,
            co_name, co_relation, (str(co_income) if co_income is not None else None),
            has_id_proof, has_addr_proof, has_income_proof, has_property_docs, declaration,
            applicant_sig, coapp_sig, application_date, place
        ))
        mysql.connection.commit()
        flash(f'Business loan application submitted. Rate {rate:.2f}% • EMI ₹{emi:.2f}', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Could not submit business loan application: {e}', 'danger')
    return redirect(url_for('userdashloan'))
 
 
# ========== USER: VIEW LOANS ==========
@app.route('/view_loans')
def view_loans():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name FROM bank_users WHERE email=%s", (email,))
    user = cur.fetchone()
    if not user:
        cur.close()
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
 
    loans = []
 
    def _fetch_and_append(kind, table):
        cur.execute(f"""
            SELECT id, user_id, applicant_name, purpose,
                   interest_type, interest_rate, emi_amount,
                   loan_amount, loan_tenure_years,
                   application_date, status, updated_at
            FROM {table}
            WHERE user_id=%s
            ORDER BY application_date DESC, id DESC
        """, (user['user_id'],))
        rows = cur.fetchall() or []
        for r in rows:
            amount = r.get('loan_amount')
            tenure = r.get('loan_tenure_years')
            rate   = r.get('interest_rate')
            emi    = r.get('emi_amount')
 
            if rate is None:
                rate = _compute_interest_rate(kind, r.get('interest_type'), amount, tenure)
            if emi is None:
                emi = compute_emi(amount, rate, tenure)
 
            loans.append({
                'loan_kind': kind,
                'loan_type_label': 'Home Loan' if kind=='home' else ('Personal Loan' if kind=='personal' else 'Business Loan'),
                'purpose': r.get('purpose'),
                'interest_type': r.get('interest_type'),
                'interest_rate': rate,
                'emi_amount': emi,
                'loan_tenure_years': tenure,
                'loan_amount': amount,
                'application_date': r.get('application_date'),
                'status': r.get('status'),
                'status_label': _status_label(r.get('status')),
                'updated_at': r.get('updated_at'),
            })
 
    _fetch_and_append('home',     'home_loan_applications')
    _fetch_and_append('personal', 'personal_loan_applications')
    _fetch_and_append('business', 'business_loan_applications')
 
    cur.close()
    return render_template('view_loans.html', user=user, loans=loans)
 
 
# ========== AGENT: PROFILE & APPLY PAGES ==========

@app.route('/loanagentprofile')
def loanagentprofile():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT user_id, name, pan,dob, mobile, email,city,state,country,gender,department,status,role,password,aadhaar,deleted_date FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('agentprofile.html', user=user)


@app.route('/agentapplyloan')
def agentapplyloan():
    # just render the agent form; the POST is handled by /loan-agent/apply
    agent = _current_user()
    return render_template('loan_apply.html', user=agent)


# ========== AGENT: SUBMIT APPLICATION ==========
@app.route('/loan-agent/apply', methods=['GET', 'POST'])
def loan_agent_apply():
    agent = _current_user()
    if not agent or _user_role(agent) not in {'loan_agent', 'loanagent', 'agent_loan'}:
        flash('Only Loan Agents can access this page.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        return render_template('loan_apply.html', user=agent)
 
    f, files = request.form, request.files
    try:
        # Target customer
        customer_email = (f.get('customer_email') or '').strip().lower()
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT user_id, name FROM bank_users WHERE email=%s", (customer_email,))
        cust = cur.fetchone()
        if not cust:
            cur.close()
            flash('Customer email not found.', 'danger')
            return redirect(url_for('loan_agent_apply'))
 
        loan_kind = (f.get('loan_kind') or '').strip().lower()  # home|personal|business
        if loan_kind not in ('home', 'personal', 'business'):
            cur.close()
            flash('Please select a valid loan type.', 'danger')
            return redirect(url_for('loan_agent_apply'))
 
        # ---------- FORM FIELDS ----------
        applicant_name = (f.get('applicantName') or '').strip()
        dob            = f.get('dob') or None
        age            = f.get('age') or None
        gender         = (f.get('gender') or '').strip()
        address        = (f.get('address') or '').strip()
        pin            = (f.get('pin') or '').strip()
        telephone      = (f.get('telephone') or '').strip()
        mobile         = (f.get('mobile') or '').strip()
        nationality    = (f.get('nationality') or '').strip()
        marital_status = (f.get('maritalStatus') or '').strip()
        pan            = (f.get('pan') or '').strip()
 
        employment_type = (f.get('employmentType') or '').strip()
        company_name    = (f.get('companyName') or '').strip()
        designation     = (f.get('designation') or '').strip()
        gross_income    = Decimal(f.get('grossIncome') or '0')
        experience      = int(f.get('experience') or 0)
        current_exp     = f.get('currentExp')
        current_exp     = int(current_exp) if current_exp else None
 
        # Property only for home
        property_address = (f.get('propertyAddress') or '').strip() if loan_kind == 'home' else ''
        property_type    = (f.get('propertyType') or '').strip()    if loan_kind == 'home' else ''
        property_age     = int(f.get('propertyAge') or 0) if (loan_kind == 'home' and f.get('propertyAge')) else None
        built_up_area    = int(f.get('builtUpArea') or 0) if loan_kind == 'home' else 0
        property_value   = Decimal(f.get('propertyValue') or '0') if loan_kind == 'home' else Decimal('0')
        builder_name     = (f.get('builderName') or '').strip() if loan_kind == 'home' else ''
 
        loan_amount      = Decimal(f.get('loanAmount') or '0')
        loan_tenure      = int(f.get('loanTenure') or 0)
        purpose          = (f.get('purpose') or (loan_kind if loan_kind!='home' else 'dream-home')).strip()
        interest_type    = (f.get('interestType') or '').strip().title()
 
        existing_loan    = Decimal(f.get('existingLoan') or '0')
        other_loan       = Decimal(f.get('otherLoan') or '0')
        credit_card      = Decimal(f.get('creditCard') or '0')
        savings          = Decimal(f.get('savings') or '0')
        other_assets     = Decimal(f.get('otherAssets') or '0')
 
        bank_name        = (f.get('bankName') or '').strip()
        account_number   = (f.get('accountNumber') or '').strip()
        account_type     = (f.get('accountType') or '').strip()
        account_years    = int(f.get('accountYears') or 0)
 
        co_name          = (f.get('coApplicantName') or '').strip()
        co_relation      = (f.get('coApplicantRelation') or '').strip()
        co_income        = f.get('coApplicantIncome')
        co_income        = Decimal(co_income) if co_income else None
 
        has_id_proof     = 1 if f.get('idProof') else 0
        has_addr_proof   = 1 if f.get('addressProof') else 0
        has_income_proof = 1 if f.get('incomeProof') else 0
        has_property_docs= 1 if f.get('propertyDocs') else 0
        declaration      = 1 if f.get('declaration') else 0
 
        applicant_sig    = save_upload(files.get('applicantSignature'), 'signatures')
        coapp_sig        = save_upload(files.get('coApplicantSignature'), 'signatures')
 
        application_date = f.get('date') or datetime.today().strftime('%Y-%m-%d')
        place            = (f.get('place') or '').strip()
 
        # Rate/EMI
        rate = _compute_interest_rate(loan_kind, interest_type, loan_amount, loan_tenure)
        emi  = _compute_emi(loan_amount, rate, loan_tenure)
 
        # ---------- TABLE MAPPING ----------
        table = {
            'home': 'home_loan_applications',
            'personal': 'personal_loan_applications',
            'business': 'business_loan_applications'
        }[loan_kind]
 
        # ---------- GENERATE UNIQUE REQUEST ID ----------
        request_id = generate_loan_request_id()  # LRxxxxx
 
        # ---------- INSERT INTO LOAN-SPECIFIC TABLE ----------
        cols = ["request_id","user_id","applicant_name","dob","age","gender","address","pin","telephone","mobile","nationality",
                "marital_status","pan","employment_type","company_name","designation","gross_annual_income",
                "total_experience_years","current_company_experience_years","property_address","property_type",
                "property_age_years","built_up_area_sqft","property_value","loan_amount","loan_tenure_years",
                "builder_name","purpose","interest_type"]
 
        vals = [request_id, cust['user_id'], applicant_name, dob, age, gender, address, pin, telephone, mobile, nationality,
                marital_status, pan, employment_type, company_name, designation, str(gross_income),
                experience, current_exp, property_address, property_type,
                property_age, built_up_area, str(property_value), str(loan_amount), loan_tenure,
                builder_name, purpose, interest_type]
 
        # optional interest/emi columns
        if table_has_column(table, 'interest_rate'):
            cols.append('interest_rate'); vals.append(str(rate))
        if table_has_column(table, 'emi_amount'):
            cols.append('emi_amount'); vals.append(str(emi))
 
        # remaining fields
        cols += ["existing_home_loan","other_loans","credit_card_limits","savings_investments","other_assets",
                 "bank_name","bank_account_number","bank_account_type","bank_years_with_bank",
                 "coapplicant_name","coapplicant_relationship","coapplicant_annual_income",
                 "has_id_proof","has_address_proof","has_income_proof","has_property_docs","declaration_agreed",
                 "applicant_signature_path","coapplicant_signature_path","application_date","place","status"]
 
        vals += [str(existing_loan),str(other_loan),str(credit_card),str(savings),str(other_assets),
                 bank_name,account_number,account_type,account_years,
                 co_name,co_relation,(str(co_income) if co_income is not None else None),
                 has_id_proof,has_addr_proof,has_income_proof,has_property_docs, declaration,
                 applicant_sig,coapp_sig,application_date,place,'pending_manager']
 
        # mark submitter role if column exists
        if table_has_column(table, 'submitted_by_role'):
            cols.append('submitted_by_role'); vals.append('Loan_Agent')
 
        placeholders = ",".join(["%s"] * len(vals))
        sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        cur.execute(sql, tuple(vals))
 
        # ---------- ALSO INSERT INTO loan_requests ----------
        req_cols = ["request_id","loan_type"] + cols[2:]
        req_vals = [request_id, loan_kind] + vals[2:]
 
        req_placeholders = ",".join(["%s"] * len(req_vals))
        req_sql = f"INSERT INTO loan_requests ({','.join(req_cols)}) VALUES ({req_placeholders})"
        cur.execute(req_sql, tuple(req_vals))
 
        mysql.connection.commit()
        cur.close()
 
        flash(f'{loan_kind.title()} loan application submitted for {cust["name"]}. '
              f'Rate {rate:.2f}% • EMI ₹{emi:.2f}', 'success')
 
    except Exception as e:
        mysql.connection.rollback()
        try: cur.close()
        except:
            pass
        flash(f'Could not submit application: {e}', 'danger')
 
    return redirect(url_for('loan_agent_apply'))
 


# ---------- AGENT: LOAD LOANS ----------
def _load_loans_for_agent(only_agent=True):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    loans = []

    def pull(kind, table):
        has_role = table_has_column(table, 'submitted_by_role')
        has_rate = table_has_column(table, 'interest_rate')
        has_emi  = table_has_column(table, 'emi_amount')

        sel = [
            "t.id", "t.user_id", "u.name AS customer_name",
            "t.loan_amount", "t.loan_tenure_years", "t.interest_type",
            "t.application_date", "t.status", "t.updated_at"
        ]
        if has_rate: sel.append("t.interest_rate")
        if has_emi:  sel.append("t.emi_amount")

        sql = f"""
            SELECT {", ".join(sel)}
            FROM {table} t
            LEFT JOIN bank_users u ON u.user_id = t.user_id
        """
        where = []
        params = []
        if only_agent and has_role:
            where.append("t.submitted_by_role=%s")
            params.append('Loan_Agent')
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY t.application_date DESC, t.id DESC"

        cur.execute(sql, tuple(params))
        for r in cur.fetchall() or []:
            rate = r.get('interest_rate')
            emi  = r.get('emi_amount')
            if rate is None:
                rate = _compute_interest_rate(kind, r.get('interest_type'), r.get('loan_amount'), r.get('loan_tenure_years'))
            if emi is None:
                emi  = _compute_emi(r.get('loan_amount'), rate, r.get('loan_tenure_years'))

            loans.append({
                'loan_kind': kind,
                'loan_type_label': 'Home Loan' if kind=='home' else ('Personal Loan' if kind=='personal' else 'Business Loan'),
                'customer_user_id': r.get('user_id'),
                'customer_name': r.get('customer_name') or '—',
                'loan_amount': r.get('loan_amount') or 0,
                'loan_tenure_years': r.get('loan_tenure_years') or 0,
                'interest_type': r.get('interest_type'),
                'interest_rate': rate,
                'emi_amount': emi,
                'application_date': r.get('application_date'),
                'status': r.get('status'),
                'status_label': _status_label(r.get('status')),
                'updated_at': r.get('updated_at'),
            })

    pull('home',     'home_loan_applications')
    pull('personal', 'personal_loan_applications')
    pull('business', 'business_loan_applications')
    cur.close()

    # If filtered by agent and got none (e.g., column missing), fall back to all
    if only_agent and len(loans) == 0:
        return _load_loans_for_agent(only_agent=False)
    return loans


# ========== AGENT: VIEW LOANS ==========
@app.route('/agent/loans')
def agent_view_loans():
    agent = _current_user()
    if not agent or _user_role(agent) not in {'loan_agent', 'loanagent', 'agent_loan'}:
        flash('Only Loan Agents can view this page.', 'danger')
        return redirect(url_for('login'))
    loans = _load_loans_for_agent(only_agent=True)
    return render_template('agent_view_loans_simple.html', loans=loans)


# Keep this route if your UI links here; it now loads data as well.
@app.route('/agentloanapproval')
def agentloanapproval():
    agent = _current_user()
    if not agent or _user_role(agent) not in {'loan_agent', 'loanagent', 'agent_loan'}:
        flash('Only Loan Agents can view this page.', 'danger')
        return redirect(url_for('login'))
    loans = _load_loans_for_agent(only_agent=True)
    return render_template('agent_view_loans_simple.html', loans=loans)


@app.route('/loanperformance')
def loanperformance():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('loanperformance.html',user=user)



@app.route('/approve_loan/<request_id>', methods=['POST'])
def approve_loan(request_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # Get loan type
    cur.execute("SELECT loan_type FROM loan_requests WHERE request_id=%s", (request_id,))
    loan_req = cur.fetchone()
    if not loan_req:
        flash("Loan request not found", "danger")
        return redirect(url_for('manage_loans'))
   
    loan_type = loan_req['loan_type'].lower()
 
    # Update loan_requests
    cur.execute("""
        UPDATE loan_requests
        SET status='Approved', updated_at=NOW()
        WHERE request_id=%s
    """, (request_id,))
 
    # Map loan type to table
    table_map = {
        'home': 'home_loan_applications',
        'personal': 'personal_loan_applications',
        'business': 'business_loan_applications'
    }
 
    # Update respective loan table
    if loan_type in table_map:
        cur.execute(f"""
            UPDATE {table_map[loan_type]}
            SET status='Approved'
            WHERE request_id=%s
        """, (request_id,))
        if cur.rowcount == 0:
            flash(f"⚠ No matching record in {table_map[loan_type]} for request_id {request_id}", "warning")
 
    mysql.connection.commit()
    cur.close()
 
    flash("Loan Approved successfully", "success")
    return redirect(url_for('manage_loans'))
 
 
@app.route('/reject_loan/<request_id>', methods=['POST'])
def reject_loan(request_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # Get loan type
    cur.execute("SELECT loan_type FROM loan_requests WHERE request_id=%s", (request_id,))
    loan_req = cur.fetchone()
    if not loan_req:
        flash("Loan request not found", "danger")
        return redirect(url_for('manage_loans'))
   
    loan_type = loan_req['loan_type'].lower()
 
    # Update loan_requests
    cur.execute("""
        UPDATE loan_requests
        SET status='Rejected', updated_at=NOW()
        WHERE request_id=%s
    """, (request_id,))
 
    # Map loan type to table
    table_map = {
        'home': 'home_loan_applications',
        'personal': 'personal_loan_applications',
        'business': 'business_loan_applications'
    }
 
    # Update respective loan table
    if loan_type in table_map:
        cur.execute(f"""
            UPDATE {table_map[loan_type]}
            SET status='Rejected'
            WHERE request_id=%s
        """, (request_id,))
        if cur.rowcount == 0:
            flash(f"⚠ No matching record in {table_map[loan_type]} for request_id {request_id}", "warning")
 
    mysql.connection.commit()
    cur.close()
 
    flash("Loan Request has been Rejected", "success")
    return redirect(url_for('manage_loans'))
  
 


   
#Dashboard - user->Investment

@app.route('/userdashinvest')
def userdashinvest():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('userdashinvest.html',user=user)

# ========== FIXED: userpfform now handles POST and inserts into DB ==========

#Dashboard - user->Investment
def _role(u:dict) -> str:
    return (u.get('role') or session.get('user_role') or '').strip()
 
def _current_user():
    """
    Works with either session['user_id'] or session['user_email'].
    """
    uid = session.get('user_id')
    email = session.get('user_email')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if uid:
            cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (uid,))
        elif email:
            cur.execute("SELECT * FROM bank_users WHERE email=%s", (email,))
        else:
            return None
        return cur.fetchone()
    finally:
        cur.close()
 
def _status_label(s):
    return {
        'pending_manager': 'Pending',
        'approved': 'Approved',
        'declined': 'Declined',
        'issued': 'Issued',
        'active': 'Active',
        'closed': 'Closed',
    }.get((s or '').lower(), s or '—')
 
def _gen_inv_app_no() -> str:
    """
    INV + YYMMDD + '-' + 4-hex, e.g., INV250912-7A3F
    """
    return f"INV{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
 
def _canon_invest_type(raw: str) -> str:
    s = (raw or "").strip().lower()
    if "provident" in s or "ppf" in s: return "PPF"
    if "bond" in s or "frsb" in s or "saving bond" in s: return "FRSB"
    if "pension" in s or "nps" in s: return "NPS"
    return (raw or "PPF")
 
def _parse_years(raw: str) -> int:
    if raw is None: return 0
    m = re.search(r'(\d+)', str(raw))
    return int(m.group(1)) if m else 0

def generate_invest_request_id():
    """
    Generate unique IR + 3 digit request id for investments
    """
    cur = mysql.connection.cursor()
    while True:
        rid = "IR" + f"{random.randint(0, 999):03d}"
        cur.execute("SELECT 1 FROM investment_applications WHERE request_id=%s", (rid,))
        if not cur.fetchone():
            break
    cur.close()
    return rid
 
# ========== Your existing dashboard route (unchanged) ==========
 

 
 
@app.route('/userpfform', methods=['GET', 'POST'])
def userpfform():
    user = _current_user()
    if not user:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        # Render your existing user investment form
        return render_template('invest_apply_user.html', user=user)
 
    # POST -> insert investment application
    f = request.form
    try:
        full_name   = (f.get('full_name') or '').strip()
        pan         = (f.get('pan') or '').strip()
        initial_dep = Decimal(f.get('initial_deposit') or '0')
        inv_type_ui = (f.get('investment_type') or '').strip()
        inv_type    = _canon_invest_type(inv_type_ui)
        tenure_yrs  = _parse_years(f.get('investment_tenure') or '')
        app_date    = datetime.today().strftime('%Y-%m-%d')
 
        if not full_name or not pan or initial_dep <= 0 or tenure_yrs <= 0:
            raise ValueError("Please fill all required fields with valid values.")
 
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
        # ensure table exists (optional safety; remove if you already created it)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS investment_applications (
              id INT AUTO_INCREMENT PRIMARY KEY,
              application_number VARCHAR(24) NOT NULL UNIQUE,
              user_id VARCHAR(100) NOT NULL,
              full_name VARCHAR(150) NOT NULL,
              pan VARCHAR(20) NOT NULL,
              initial_deposit DECIMAL(12,2) NOT NULL,
              investment_type VARCHAR(60) NOT NULL,
              investment_tenure_years INT NOT NULL,
              application_date DATE NOT NULL,
              submitted_by_role ENUM('User','Investment_Agent') NOT NULL DEFAULT 'User',
              submitted_by_user_id VARCHAR(100) NULL,
              status ENUM('pending_manager','approved','declined','active','closed')
                     NOT NULL DEFAULT 'pending_manager',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
              INDEX idx_inv_user (user_id),
              INDEX idx_inv_status (status, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
 
        # generate a unique application number (retry on rare collision)
        for _ in range(3):
            app_no = _gen_inv_app_no()
            req_id = generate_invest_request_id()
            try:
                cur.execute("""
                    INSERT INTO investment_applications
                    (application_number, request_id, user_id, full_name, pan, initial_deposit,
                    investment_type, investment_tenure_years, application_date,
                    submitted_by_role, submitted_by_user_id, status)
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,'User',%s,'pending_manager')
                """, (app_no, req_id, user['user_id'], full_name, pan,
                    str(initial_dep), inv_type, tenure_yrs, app_date, user['user_id']))
                mysql.connection.commit()
                break
            except Exception as e:
                mysql.connection.rollback()
                # try again on unique collision
                if "Duplicate" in str(e) or "UNIQUE" in str(e):
                    continue
                raise
 
        cur.close()
        flash(f'Investment application submitted successfully. Ref {app_no}', 'success')
    except Exception as e:
        try: cur.close()
        except: pass
        mysql.connection.rollback()
        flash(f'Could not submit investment application: {e}', 'danger')
 
    # Back to the same form
    return redirect(url_for('userpfform'))

@app.route('/investperformance')
def investperformance():
    user_id = session.get('user_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('investperformance.html',user=user)
 
 
# ---------- USER: Apply for Investment ----------
 
@app.route('/investments/apply', methods=['GET', 'POST'])
def invest_apply():
    user = _current_user()
    if not user:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        return render_template('invest_apply_user.html', user=user)
 
    # POST
    f = request.form
    try:
        full_name   = (f.get('full_name') or f.get('Full Name') or '').strip()
        pan         = (f.get('pan') or f.get('PAN Number') or '').strip()
        initial_dep = Decimal(f.get('initial_deposit') or f.get('Initial Deposit Amount (₹)') or '0')
        inv_type    = _canon_invest_type(f.get('investment_type') or f.get('Investment Type'))
        tenure_yrs  = _parse_years(f.get('investment_tenure') or f.get('Investment Tenure'))
        app_date    = datetime.today().strftime('%Y-%m-%d')
 
        if initial_dep <= 0:
            raise ValueError("Initial deposit must be greater than 0.")
 
        # Insert with unique application number (retry if collision)
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        for _ in range(3):
            app_no = _gen_inv_app_no()
            req_id = generate_invest_request_id()
            try:
                cur.execute("""
                    INSERT INTO investment_applications
                    (application_number, request_id, user_id, full_name, pan, initial_deposit,
                    investment_type, investment_tenure_years, application_date,
                    submitted_by_role, submitted_by_user_id, status)
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,'User',%s,'pending_manager')
                """, (app_no, req_id, user['user_id'], full_name, pan,
                    str(initial_dep), inv_type, tenure_yrs, app_date, user['user_id']))
                mysql.connection.commit()
                break
            except Exception as e:
                # Duplicate application_number? regenerate and retry once more
                mysql.connection.rollback()
                if "Duplicate" in str(e) or "UNIQUE" in str(e):
                    continue
                raise
 
        cur.close()
        flash(f'Investment application submitted. Ref {app_no}', 'success')
    except Exception as e:
        try: cur.close()
        except: pass
        mysql.connection.rollback()
        flash(f'Could not submit investment application: {e}', 'danger')
 
    return redirect(url_for('invest_apply'))
 
 
# ---------- AGENT: Apply for Investment on behalf of customer ----------


 
@app.route('/investment-agent/apply', methods=['GET', 'POST'])
def invest_agent_apply():
    agent = _current_user()
    if not agent or _role(agent).lower() not in {'investment_agent', 'investment agent', 'investment-agent'}:
        flash('Only Investment Agents can access this page.', 'danger')
        return redirect(url_for('login'))
 
    if request.method == 'GET':
        return render_template('invest_apply_agent.html', user=agent)
 
    f = request.form
    try:
        # Find the customer (target) by email
        customer_email = (f.get('customer_email') or '').strip().lower()
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT user_id, name FROM bank_users WHERE email=%s", (customer_email,))
        cust = cur.fetchone()
        if not cust:
            cur.close()
            flash('Customer email not found.', 'danger')
            return redirect(url_for('invest_agent_apply'))
 
        # Read form fields
        full_name   = (f.get('full_name') or f.get('Full Name') or '').strip()
        pan         = (f.get('pan') or f.get('PAN Number') or '').strip()
        initial_dep = Decimal(f.get('initial_deposit') or f.get('Initial Deposit Amount (₹)') or '0')
        inv_type    = _canon_invest_type(f.get('investment_type') or f.get('Investment Type'))
        tenure_yrs  = _parse_years(f.get('investment_tenure') or f.get('Investment Tenure'))
        app_date    = datetime.today().strftime('%Y-%m-%d')
 
        if initial_dep <= 0:
            raise ValueError("Initial deposit must be greater than 0.")
 
        # Insert w/ unique app number & role
        for _ in range(3):
            app_no = _gen_inv_app_no()
            req_id = generate_invest_request_id()
            try:
                cur.execute("""
                    INSERT INTO investment_applications
                    (application_number, request_id,user_id, full_name, pan, initial_deposit,
                     investment_type, investment_tenure_years, application_date,
                     submitted_by_role, submitted_by_user_id, status)
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,'Investment_Agent',%s,'pending_manager')
                """, (app_no,req_id, cust['user_id'], full_name, pan, str(initial_dep),
                      inv_type, tenure_yrs, app_date, agent['user_id']))
                mysql.connection.commit()
                break
            except Exception as e:
                mysql.connection.rollback()
                if "Duplicate" in str(e) or "UNIQUE" in str(e):
                    continue
                raise
 
        cur.close()
        flash(f'Investment application for {cust["name"]} submitted. Ref {app_no}', 'success')
    except Exception as e:
        try: cur.close()
        except: pass
        mysql.connection.rollback()
        flash(f'Could not submit investment application: {e}', 'danger')
 
    return redirect(url_for('invest_agent_apply'))
 
 
# ---------- (Optional) Agent view: minimal list of investment applications ----------
 
@app.route('/investment-agent/applications')
def invest_agent_list():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    agent = _current_user()
    if not agent or _role(agent).lower() not in {'investment_agent', 'investment agent', 'investment-agent'}:
        flash('Only Investment Agents can view this page.', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT ia.application_number, ia.user_id, u.name AS customer_name,
               ia.investment_type, ia.initial_deposit, ia.investment_tenure_years,
               ia.status, ia.application_date
        FROM investment_applications ia
        LEFT JOIN bank_users u ON u.user_id = ia.user_id
        WHERE ia.submitted_by_role = 'Investment_Agent'
        ORDER BY ia.application_date DESC, ia.id DESC
    """)
    rows = cur.fetchall() or []
    cur.close()
 
    # Normalize for template
    apps = [{
        'application_number': r['application_number'],
        'customer_user_id': r['user_id'],
        'customer_name': r.get('customer_name') or '—',
        'investment_type': r['investment_type'],
        'initial_deposit': r['initial_deposit'],
        'tenure_years': r['investment_tenure_years'],
        'status': r['status'],
        'status_label': _status_label(r['status']),
        'application_date': r['application_date'],
    } for r in rows]
 
    return render_template('agent_view_investments.html', apps=apps,user=user)
 
 
 
@app.route('/view_investments')
def view_investments():
    email = session.get('user_email')
    if not email:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # get logged-in user
    cur.execute("SELECT user_id, name FROM bank_users WHERE email=%s", (email,))
    user = cur.fetchone()
    if not user:
        cur.close()
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
 
    # fetch this user's investment applications
    cur.execute("""
        SELECT
            application_number,
            investment_type,
            investment_tenure_years,
            initial_deposit,
            status,
            submitted_by_role,
            created_at
        FROM investment_applications
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (user['user_id'],))
    investments = cur.fetchall() or []
    cur.close()
 
    return render_template('view_investments.html', user=user, investments=investments)
 
@app.route('/viewinvestments')
def viewinvestments():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT ia.id, ia.request_id, ia.application_number,
               u.name AS customer, ia.investment_type,
               ia.initial_deposit, ia.application_date,
               ia.status
        FROM investment_applications ia
        LEFT JOIN bank_users u ON u.user_id = ia.user_id
        ORDER BY ia.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return render_template('view-investments.html', investments=rows,user=user)
 
@app.post('/investments/<int:inv_id>/<string:action>')
def update_investment_status(inv_id, action):
    if action not in ('approve','reject'):
        abort(400)
    new_status = 'approved' if action == 'approve' else 'declined'
    cur = mysql.connection.cursor()
    cur.execute("UPDATE investment_applications SET status=%s WHERE id=%s",
                (new_status, inv_id))
    mysql.connection.commit()
    cur.close()
    flash('Status updated', 'success')
    return redirect(url_for('viewinvestments'))
 

#Dashboard - user->forex

@app.route('/userdashforex')
def userdashforex():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('userdashforex.html',user=user)

@app.route('/logout')
def logout():
    return render_template('index.html')

#Agent Dashboard(Card_Agent)

 
@app.route('/cardapplications', methods=['GET'])
def cardapplications():
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT user_id, role, name FROM bank_users WHERE email=%s", (email,))
    me = cur.fetchone()
    if not me:
        cur.close()
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
 
    role = (me.get('role') or '').strip()
 
    # Build WHERE clause by role
    where_sql = ""
    params = ()
    if role == 'Card_Agent':
        # Agent tracks apps they submitted
        where_sql = "WHERE submitted_by_agent_id = %s"
        params = (me['user_id'],)
    elif role == 'User':
        # End user can see their own apps
        where_sql = "WHERE (customer_user_id = %s OR submitted_by_user_id = %s)"
        params = (me['user_id'], me['user_id'])
    else:
        # Managers/TLs see everything
        where_sql = ""
        params = ()
 
    # NOTE: ensure these columns exist in `card_applications`:
    # application_ref, customer_user_id, customer_name, card_type, card_subtype,
    # status, created_at, manager_approval_date
    sql = f"""
        SELECT id, application_ref, customer_user_id, customer_name,
               card_type, card_subtype, status,
               created_at, manager_approval_date
        FROM card_applications
        {where_sql}
        ORDER BY created_at DESC, id DESC
    """
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
 
    # Decorate rows for display labels
    type_map = {'credit': 'Credit Card', 'debit': 'Debit Card', 'prepaid': 'Prepaid Card'}
    status_map = {
        'pending_manager': 'Pending',
        'approved': 'Approved',
        'issued': 'Issued',
        'declined': 'Declined'
    }
    for r in rows:
        r['card_type_label'] = type_map.get((r.get('card_type') or '').lower(), r.get('card_type'))
        r['status_label'] = status_map.get((r.get('status') or '').lower(), r.get('status') or '—')
 
    # Pass list to template; your template should render `created_at` as Applied Date
    return render_template('cardapplications.html', apps=rows, agent=me, user=user)
 
 
 

 
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


@app.route('/customer_count')
def customer_count():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(*) AS total_customers FROM bank_users WHERE role = 'User'")
    result = cur.fetchone()
    cur.close()
    return {"total_customers": result['total_customers']}
 
# --- SearchBar ---
 
@app.route('/searchprofile', methods=['GET'])
def searchprofile():
    query = request.args.get('query', '').strip()
    search_by = request.args.get('search_by', 'name')  # default to name
 
    if not query:
        flash("Please enter a search term.")
        return redirect(url_for('dashboard'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    if search_by == "user_id":
        sql = "SELECT * FROM bank_users WHERE user_id LIKE %s"
    else:  # default search by name
        sql = "SELECT * FROM bank_users WHERE name LIKE %s"
 
    like_query = f"%{query}%"
    cur.execute(sql, (like_query,))
    user = cur.fetchone()
    cur.close()
 
    if not user:
        flash("No user found.")
        return redirect(url_for('dashboard'))
 
    return render_template('searchprofile.html', user=user)
 
 
from flask import jsonify
import MySQLdb.cursors
 
@app.route('/api/user_suggestions')
def user_suggestions():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Only fetch users with role 'User'
    sql = """
        SELECT user_id, name
        FROM bank_users
        WHERE (name LIKE %s OR user_id LIKE %s)
        LIMIT 10
    """
    like_q = f"%{q}%"
    cur.execute(sql, (like_q, like_q))
    rows = cur.fetchall()
    cur.close()
 
    return jsonify(rows)
 


#Loan Agent Dashboard

# @app.route('/loanagentprofile')
# def loanagentprofile():
#     user_id = session.get('user_id')
#     cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cur.execute("SELECT user_id, name, pan,dob, mobile, email,city,state,country,gender,department,status,role,password,aadhaar,deleted_date FROM bank_users WHERE user_id=%s", (user_id,))
#     user = cur.fetchone()
#     cur.close()

#     return render_template('agentprofile.html',user=user)

# @app.route('/agentapplyloan')
# def agentapplyloan():

#     user_id = session.get('user_id')
#     cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
#     user = cur.fetchone()
#     cur.close()
#     return render_template('loan_apply.html',user=user)

# @app.route('/agentloanapproval')
# def agentloanapproval():
#     user_id = session.get('user_id')
#     cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
#     user = cur.fetchone()
#     cur.close()
#     return render_template('agentloanapproval.html',user=user)

# @app.route('/loanperformance')
# def loanperformance():
#     user_id = session.get('user_id')
#     cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cur.execute("SELECT email FROM bank_users WHERE user_id=%s", (user_id,))
#     user = cur.fetchone()
#     cur.close()
#     return render_template('loanperformance.html',user=user)

   
if __name__ == '__main__':
    app.run(debug=True)
