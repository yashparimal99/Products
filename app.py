from flask import Flask, render_template, request, redirect, url_for, flash,session
import MySQLdb
import MySQLdb.cursors
from flask_mysqldb import MySQL
from collections import defaultdict
from model import *

app = Flask(__name__)
app.secret_key = 'a3f5ea2691a8e93c05f4e90e1b8ff123'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Yash@123'
app.config['MYSQL_DB'] = 'banking_products'





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

#view user balance

# @app.route('/viewaccounts')
# def viewaccounts():
#     email = session.get('user_email')
#     cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor to access columns by name
#     cur.execute("SELECT cust_id, name, pan, email, mobile_no FROM users WHERE email = %s", (email,))
#     user = cur.fetchone()
#     cur.execute("SELECT * FROM bank_accounts WHERE cust_id = %s", (user['cust_id'],))
#     account = cur.fetchall()
#     cur.close()

#     return render_template('viewaccounts.html', account=account,user=user)

@app.route('/viewaccounts')
def viewaccounts():
    email = session.get('user_email')
    if not email:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get user details
    cur.execute("SELECT cust_id, name, pan, email, mobile_no FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    grouped_accounts = defaultdict(list)

    if user:
        # Get all bank accounts for this user
        cur.execute("SELECT * FROM bank_accounts WHERE cust_id = %s", (user['cust_id'],))
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
    cur.execute("SELECT cust_id, name, pan, email, mobile_no FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    grouped_deposits = defaultdict(list)

    if user:
         cur.execute("SELECT * FROM bank_deposits WHERE cust_id = %s", (user['cust_id'],))
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




#this is working route for login
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
#         user = cur.fetchone()
#         cur.close()
#         if user:
#             session['user_email'] = email
            
#             flash('Logged in successfully!', 'success')
#             return redirect(url_for('dashboard'))
#         else:
#             flash('Invalid email or password', 'danger')
#     return render_template('login.html')

from MySQLdb.cursors import DictCursor

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor(DictCursor)  
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_email'] = user['email']
            session['user_role'] = user['role']  
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')


# @app.route('/userlogin')
# def userlogin():
#     return render_template('login.html')





import random
import string





def generate_cust_id():
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
        cur.execute("SELECT * FROM bank_accounts WHERE account_number = %s", (account_number,))
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
        cur.execute("SELECT * FROM bank_deposits WHERE account_number = %s", (account_number,))
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






    
    
     
   
    






# generate unique Deposits Account number
# def generate_unique_deposit_account_no(account_number):
#     cur = mysql.connection.cursor()
#     while True:
#         account_number = str(random.randint(1000000000, 9999999999))
#         cur.execute("SELECT * FROM bank_deposits WHERE account_number = %s", (account_number,))
#         if not cur.fetchone():
#             break
#     return account_number


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
        cur.execute("SELECT * FROM users WHERE email = %s OR mobile_no = %s", (email, mobile_no))
        if cur.fetchone():
            flash('Email or mobile number already registered', 'danger')
        else:
            # Generate a unique cust_id
            while True:
                cust_id = generate_cust_id()
                cur.execute("SELECT * FROM users WHERE cust_id = %s", (cust_id,))
                if not cur.fetchone():  # If not found, it's unique
                    break

            # Insert user with the generated cust_id
            cur.execute(
                "INSERT INTO users (cust_id, name,pan, email, mobile_no, password) VALUES (%s, %s,%s, %s, %s, %s)",
                (cust_id, name,pan, email, mobile_no, password)
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


@app.route('/open_account', methods=['GET', 'POST'])
def open_account():
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
        return redirect(url_for('userlogin'))  # consistent redirect

    cust_id = user['cust_id']

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
        cur.execute("""
            INSERT INTO bank_accounts (
                cust_id, first_name, middle_name, last_name, email,
                mobile, aadhar, account_type, account_number
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cust_id, first_name, middle_name, last_name, email,
            mobile, aadhar, account_type, account_number
        ))
        mysql.connection.commit()
        cur.close()

        flash(f"Savings account created. Account number: {account_number}", "success")
        return redirect(url_for('dashboard'))

    return render_template('applicationform1.html', user=user)


@app.route('/open_deposits', methods=['GET', 'POST'])
def open_deposits():
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
        return redirect(url_for('login'))

    cust_id = user['cust_id']

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
        cur.execute("""
            INSERT INTO bank_deposits (
                cust_id, first_name, middle_name, last_name, email,
                mobile, aadhar, account_type, account_number
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cust_id, first_name, middle_name, last_name, email,
            mobile, aadhar, account_type, account_number
        ))
        mysql.connection.commit()
        cur.close()

        flash(f"Deposit account created. Account number: {account_number}", "success")
        return redirect(url_for('dashboard'))

    return render_template('depositform.html',user=user)



#User Dashboard

# @app.route('/dashboard')
# def dashboard():
#     email = session.get('user_email')
#     if not email:
#         flash('Please login first', 'danger')
#         return redirect(url_for('userlogin'))

#     cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor to access columns by name
#     cur.execute("SELECT cust_id, name, pan, email, mobile_no FROM users WHERE email = %s", (email,))
#     user = cur.fetchone()

    # cur.execute("SELECT * FROM bank_accounts WHERE cust_id = %s", (user['cust_id'],))
    # account = cur.fetchone()

    # cur.execute("SELECT * FROM bank_deposits WHERE cust_id = %s", (user['cust_id'],))
    # deposits = cur.fetchone()



    # cur.close()

    # if not user:
    #     flash("User not found.", "danger")
    #     return redirect(url_for('login'))

    # return render_template('userdashboard.html', user=user)
@app.route('/dashboard')
def dashboard():
    role = session.get('user_role')
    email = session.get('user_email')

    if not role or not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    # Fetch the full user details
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    templates = {
        'user': 'userdashboard.html',
        'tl': 'TLdashboard.html',
        'manager': 'managerdashboard.html'
    }

    return render_template(templates.get(role, 'login.html'), user=user)


#Manager Dasboard Routes

@app.route('/manageaccounts')
def manageaccounts():
    return render_template('manageaccounts.html')

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

@app.route('/quicktransfer')
def quicktransfer():
    return render_template('quicktransfer.html')

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



    
if __name__ == '__main__':
    app.run(debug=True)
