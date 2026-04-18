from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from mpesa import stk_push

app = Flask(__name__)
app.secret_key = "secretkey"

# DATABASE CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --------------------
# DATABASE MODELS
# --------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    status = db.Column(db.String(50), default="Pending")

    total_repayment = db.Column(db.Integer)

# --------------------
# ROUTES
# --------------------
from functools import wraps

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return wrap

@app.route('/')
def home():
    return render_template('home.html')
@app.route('/pay-loan/<int:loan_id>', methods=['POST'])
@login_required
def pay_loan(loan_id):
    loan = Loan.query.get(loan_id)

    phone = request.form['phone']
    amount = loan.total_repayment

    response = stk_push(phone, amount)

    return str(response)

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form['password'])

        new_user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()

        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect('/dashboard')

    return render_template('login.html')

# DASHBOARD
@app.route('/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_loans = Loan.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', loans=user_loans)
@app.route('/dashboard')
@login_required
def dashboard():
    user_loans = Loan.query.filter_by(user_id=session['user_id']).all()

    # Get payments for those loans
    payments = Payment.query.all()

    return render_template('dashboard.html', loans=user_loans, payments=payments)

# APPLY LOAN
@app.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    if request.method == 'POST':
        amount = int(request.form['amount'])
        duration = int(request.form['duration'])

        interest_rate = 0.10  # 10% per month
        total = amount + (amount * interest_rate * duration)

        loan = Loan(
            user_id=session['user_id'],
            amount=amount,
            duration=duration,
            total_repayment=int(total)
        )

        db.session.add(loan)
        db.session.commit()

        return redirect('/dashboard')

    return render_template('apply.html')
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'))
    phone = db.Column(db.String(20))
    amount = db.Column(db.Integer)
    status = db.Column(db.String(50), default="Pending")
# M-PESA
@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()

    print("M-Pesa Callback Received:", data)

    # Extract payment result
    try:
        result = data['Body']['stkCallback']['ResultCode']

        if result == 0:
            print("Payment Successful")
        else:
            print("Payment Failed")

    except Exception as e:
        print("Error parsing callback:", e)

    return "OK"
@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()

    try:
        callback = data['Body']['stkCallback']
        result_code = callback['ResultCode']

        if result_code == 0:
            metadata = callback['CallbackMetadata']['Item']

            amount = metadata[0]['Value']
            phone = metadata[4]['Value']

            # Find latest loan for now (simple logic)
            loan = Loan.query.order_by(Loan.id.desc()).first()

            # Save payment
            payment = Payment(
                loan_id=loan.id,
                phone=phone,
                amount=amount,
                status="Completed"
            )

            db.session.add(payment)

            # Mark loan as PAID
            loan.status = "PAID"

            db.session.commit()

            print("Payment saved and loan updated")

    except Exception as e:
        print("Callback error:", e)

    return "OK"

# LOGOUT
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

# ADMIN LOGIN (simple version)
# --------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple hardcoded admin (we will improve later)
        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect('/admin/dashboard')

    return render_template('admin_login.html')


# --------------------
# ADMIN DASHBOARD
# --------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    all_loans = Loan.query.all()
    return render_template('admin_dashboard.html', loans=all_loans)


# --------------------
# APPROVE LOAN
# --------------------
@app.route('/approve/<int:loan_id>')
def approve_loan(loan_id):
    if 'admin' not in session:
        return redirect('/admin')

    loan = Loan.query.get(loan_id)
    loan.status = "Approved"
    db.session.commit()

    return redirect('/admin/dashboard')


# --------------------
# REJECT LOAN
# --------------------
@app.route('/reject/<int:loan_id>')
def reject_loan(loan_id):
    if 'admin' not in session:
        return redirect('/admin')

    loan = Loan.query.get(loan_id)
    loan.status = "Rejected"
    db.session.commit()

    return redirect('/admin/dashboard')
@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    ...

# -----------------------------
# ALWAYS LAST
# -----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run()