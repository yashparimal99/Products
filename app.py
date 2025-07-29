from flask import Flask, render_template, request, redirect, url_for, flash,session
import MySQLdb
from flask_mysqldb import MySQL


app = Flask(__name__)
app.secret_key = 'a3f5ea2691a8e93c05f4e90e1b8ff123'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Yash@123'
app.config['MYSQL_DB'] = 'banking_products'



mysql = MySQL(app)


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
    return render_template('cards.html')

@app.route('/creditcard')
def creditcard():
    return render_template('creditcard.html')

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

@app.route('/loanscards')
def loanscards():
    return render_template('loan-cards.html')

@app.route('/homeloanform')
def homeloanform():
    return render_template('home_loan_form.html')

@app.route('/loanpersonal')
def loanpersonal():
    return render_template('Loan_personal.html')

@app.route('/business_loans')
def business_loans():
    return render_template('Business_Loan.html')


#forex

@app.route('/forex')
def forex():
    return render_template('forex.html')
 
@app.route('/travel_forex')
def travel_forex():
    return render_template('travel-forex.html')
 
@app.route('/travel_forex_form')
def travel_forex_form():
    return render_template('travel-forex-form.html')
 
@app.route('/send_money_abroad')
def send_money_abroad():
    return render_template('send-money-abroad.html')
 
@app.route('/send_money_abroad_form')
def send_money_abroad_form():
    return render_template('send-money-abroad-form.html')
 
@app.route('/send_money_india')
def send_money_india():
    return render_template('send-money-india.html')  
 
@app.route('/send_money_india_form')
def send_money_india_form():
    return render_template('send-money-india-form.html')    
 
@app.route('/currency_exchange')
def currency_exchange():
    return render_template('currency-exchange.html')
 
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





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()
        if user:
            session['user_email'] = email
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')





# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         name = request.form['fname']
#         email = request.form['email']
#         mobileno = request.form['mn']
#         password = request.form['password']

#         cur = mysql.connection.cursor()

#         # Check if email or mobile already exists
#         cur.execute("SELECT * FROM users WHERE email = %s OR mobileno = %s", (email, mobileno))
#         if cur.fetchone():
#             flash('Email or mobile number already registered', 'danger')
#         else:
#             cur.execute(
#                 "INSERT INTO users (name, email, mobileno, password) VALUES (%s, %s, %s, %s)",
#                 (name, email, mobileno, password)
#             )
#             mysql.connection.commit()
#             cur.close()
            
#             flash('Account created! Please log in.', 'success')
#             return redirect(url_for('login'))

#         cur.close()

#     return render_template('signup.html')

import random
import string

def generate_cust_id():
    """Generate a random 8-character alphanumeric customer ID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


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
            
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))

        cur.close()

    return render_template('signup.html')



@app.route('/dashboard')
def dashboard():
   email = session.get('user_email')
   if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
   return render_template('dashboard.html', email=email)

   

@app.route('/logout')
def logout():
    return render_template('index.html')



    
if __name__ == '__main__':
    app.run(debug=True)
