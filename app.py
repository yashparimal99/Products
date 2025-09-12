from flask import Flask, render_template, request, redirect, url_for, flash,session,jsonify
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
 
    my_accounts = get_accounts_for_email(email)
 
    if request.method == "POST":
        from_account  = request.form.get("from_account")      # dropdown in your paybill form
        to_account    = request.form.get("to_account")
        re_to_account = request.form.get("re_to_account")
        amount_str    = request.form.get("amount")
        remark        = (request.form.get("remark") or "").strip()
 
        # If user didn't type to_account fields, use the selected dropdown
        if (not to_account) and from_account:
            to_account = from_account
        if (not re_to_account) and from_account:
            re_to_account = from_account
 
        if not to_account or not re_to_account or not amount_str:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("deposit"))
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
        FROM_SENTINEL = 'CASH'  # avoids NOT NULL errors on transactions.from_account
 
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
        'Invest_Agent': 'investagent_dashboard.html'
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
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM accounts_requests WHERE status_flag IS NULL")
    requests = cur.fetchall()
    cur.close()
    return render_template("manage-accounts.html", requests=requests)
 
 
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
    return render_template('manviewdeposits.html', deposits=deposits)
 
 
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
    return render_template('manage-loans.html')

@app.route('/view_investments')
def view_investments():
    return render_template('view-investments.html')

@app.route('/viewcards')
def viewcards():
    email = session.get('user_email')
    if not email:
        flash("Please login first", "danger")
        return redirect(url_for("login"))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
 
    # ✅ Only fetch pending requests
    cur.execute("""
        SELECT r.request_id, r.customer_name, r.customer_email, r.card_type, r.card_subtype,
               r.submitted_by_role, r.application_ref, r.created_at, r.status_flag,
               a.id AS app_id
        FROM card_requests r
        LEFT JOIN card_applications a
          ON r.application_ref = a.application_ref
        WHERE r.status_flag IS NULL
        ORDER BY r.created_at DESC
    """)
    requests = cur.fetchall()
    cur.close()
 
    return render_template("view-cards.html", requests=requests)
 
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
    return render_template('staff-management.html')

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

ALLOWED_CARD_TYPES     = {'credit', 'debit', 'prepaid'}
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
 
 



@app.route('/open_cards', methods=['GET', 'POST'])
def open_cards():
    """
    USER flow:
    - Credit: account optional
    - Debit/Prepaid: account required (and must belong to user)
    - Derive issue_limit from CIBIL for credit; 0 otherwise
    - Generate card_number + cvv
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
        preset = (request.args.get('preset') or '').lower()
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
        flash('Please fill all required fields.', 'danger'); return redirect(url_for('open_cards'))
 
    if card_type not in ALLOWED_CARD_TYPES:
        flash('Invalid card type selected.', 'danger'); return redirect(url_for('open_cards'))
    if card_subtype not in ALLOWED_CARD_NETWORKS:
        flash('Invalid card network selected.', 'danger'); return redirect(url_for('open_cards'))
 
    # Account requirement
    if card_type in ('debit', 'prepaid'):
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
        employment_type = None
 
    full_name = ' '.join([p for p in [first_name, middle_name, last_name] if p]).strip()
    applicant_pan = user.get('pan')
 
    # Generate card number & CVV
    gen_card_number = generate_network_card_number(card_subtype)
    gen_cvv         = generate_cvv()
 
    try:
        mysql.connection.begin()
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
            'User', None, user['user_id'],
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
    """
    CARD AGENT flow:
    - Credit: account optional; Debit/Prepaid: account required
    - Derive issue_limit from CIBIL for credit; 0 otherwise
    - Generate card_number + cvv
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
    applicant_pan     = (request.form.get('panNumber') or '').strip()  # format free per your request
 
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
 
    # Account requirement
    if card_type in ('debit', 'prepaid'):
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
 
   
    return render_template('cardagent_dashboard.html')
  
 

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
    return render_template('paybill.html')



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

@app.route('/homeloan')
def homeloan():
    return render_template('userhomeapply.html')

@app.route('/userpersonalloan')
def userpersonalloan():
    return render_template('userpersonalloan.html')

@app.route('/userbusinessloan')
def userbusinessloan():
    return render_template('userbusinessloan.html')

   
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

@app.route('/userpfform')
def userpfform():
    user_id = session.get('user_id')
    # session['cust_id'] = user['cust_id']
    # print("Logged in cust_id:", cust_id)   # debug
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bank_users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('userpfform.html',user=user)



@app.route('/logout')
def logout():
    return render_template('index.html')

#Agent Dashboard(Card_Agent)



@app.route('/cardapplications', methods=['GET'])
def cardapplications():
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
               card_type, card_subtype, status_flag,
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
        None : 'Pending',
        'A': 'Approved',
        'issued': 'Issued',
        'R': 'Declined'
    }
    for r in rows:
        r['card_type_label'] = type_map.get((r.get('card_type') or '').lower(), r.get('card_type'))
        r['status_label'] = status_map.get((r.get('status_flag') or '').lower(), r.get('status_flag') or '—')
 
    # Pass list to template; your template should render `created_at` as Applied Date
    return render_template('cardapplications.html', apps=rows, agent=me)
 
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

# @app.route('/loanagentprofile')
# def loanagentprofile():
#     user_id = session.get('user_id')
#     cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cur.execute("SELECT user_id, name, pan,dob, mobile, email,city,state,country,gender,department,status,role,password,aadhaar,deleted_date FROM bank_users WHERE user_id=%s", (user_id,))
#     user = cur.fetchone()
#     cur.close()

#     return render_template('agentprofile.html',user=user)

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
