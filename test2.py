@app.route('/accountbal')
def accountbal():
    email = session.get('user_email')
    if not email:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT a.account_type, a.account_number, a.balance
        FROM bank_accounts a
        JOIN users u ON u.cust_id = a.cust_id
        WHERE u.email=%s
        ORDER BY a.account_type, a.account_number
    """, (email,))
    accts = cur.fetchall()
 
    total = sum((Decimal(str(acc['balance'])) if acc['balance'] is not None else Decimal('0.00')) for acc in accts)
 
    # pass user
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
 
    return render_template('balance.html', accounts=accts, total_balance=total, user=user)