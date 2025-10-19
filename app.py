import os
from datetime import timedelta
from PIL import Image
from flask import Flask, render_template, redirect, flash, request, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from models import db, User, Product, Cart, TransactionHistory
from forms import RegistrationForm, LoginForm, AdminRoleSetupForm, ProductsForm, ProfileForm
from flask_migrate import Migrate

# APP CONFIGURATION
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.sqlite'   # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False               # Disable modification tracking
app.config["SECRET_KEY"] = "test"                             # Secret key for sessions and CSRF
app.permanent_session_lifetime = timedelta(days=7)
db.init_app(app)
migrate = Migrate(app, db)
# Creating necessary instances
bcrypt = Bcrypt(app)
login_manager = LoginManager(app) 
login_manager.login_view = 'login' # Setting up login route
login_manager.login_message = 'Please login to view this page.'
login_manager.login_message_category = 'danger'

# Used to load user in the session.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class Utility():
    @staticmethod
    def hash_password(pw):
        return bcrypt.generate_password_hash(pw).decode('utf-8')
    
    @staticmethod
    def check_password(hashed_pw, pw):
        return bcrypt.check_password_hash(hashed_pw, pw)
    
    def save_picture(picture, *, product_id=None, user_id=None):
        ext = os.path.splitext(picture.filename)[-1]
        img = Image.open(picture)
        img.thumbnail((200,200))
        if product_id:
            path = os.path.join(app.root_path, 'static/images/products', f'{str(product_id)+ext}')
            img.save(path)
            return f'{str(product_id)+ext}'         
        elif user_id:
            path = os.path.join(app.root_path, 'static/images/profile_pictures', f'{str(user_id)+ext}')
            img.save(path)
            return f'{str(user_id)+ext}'
        else:
            return

# Home Route

@app.route("/")
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)

# SEARCH PRODUCTS BY NAME
@app.route('/search/product', methods=['GET', 'POST'])
def search_product():
    ids = session.get('searched_products_id')
    products=[]
    if ids:
        for id in ids:
            products.append(Product.query.get(id))
        session.pop('searched_products_id')
    print(products, ids)
    print(ids)

    if request.method=='POST':
        name = request.form['search']
        products = Product.query.all()
        requiredProductsID = [product.id for product in products if name in product.name.lower()]
        session['searched_products_id'] = requiredProductsID
        return redirect('/search/product')
    return render_template('searchproduct.html', products=products)

# BASIC USER AUTHENTICATION LOGICS

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if current_user.is_authenticated:
        return redirect('/')
    
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password=Utility.hash_password(form.pw.data))
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created, please login.', 'success')
        return redirect('/login')
    return render_template('register.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect('/')
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if Utility.check_password(user.password, form.pw.data):
            login_user(user)
            session.permanent = True
            flash("Successfully logged in.", "success")
            return redirect('/')
        else:
            flash("Invalid Password.", "danger")
            return redirect('/login')
    return render_template('login.html', form=form)

@app.route('/reset/password', methods=['GET', 'POST'])
def reset_password():
    if request.method=='POST':
        old_pw = request.form['opw']
        new_pw = request.form['npw']
        confirm_new_pw = request.form['cnpw']
        
        if not Utility.check_password(current_user.password, old_pw):
            flash('Incorrect password, please try again.', 'danger')
            return redirect('/profile')
        
        if new_pw!=confirm_new_pw:
            flash('Passwords do not match.', 'danger')
            return redirect('/profile')
        
        hashed_pw = Utility.hash_password(new_pw)
        current_user.password = hashed_pw
        db.session.commit()
        logout_user()
        flash('Password changed successfully, please login.', 'success')
        return redirect('/login')
    
    return redirect('/profile')

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Succesfully logged out.', 'success')
        return redirect('/login')

# ADMIN PANEL

@login_required
@app.route('/admin', methods=["GET", "POST"])
def admin_panel():
    if current_user.role!='admin':
        flash("You are not an admin", "danger")
        return redirect('/')
    
    form = AdminRoleSetupForm()
    userData = None
    if form.validate_on_submit():
        userData = User.query.filter_by(username=form.search.data).first()
        if userData:
            return render_template('dashboard.html', form=form, userData=userData, users=User.query.all(), products=Product.query.all())
        else:
            flash("User not found in the database.", 'danger')
            return redirect('/admin')
    return render_template('dashboard.html', form=form, userData=userData, users=User.query.all(), products=Product.query.all())

# Change User's role
@app.route('/admin/set/role/<string:role>/<string:username>')
def set_role(role, username):
    # Checking if the user is admin or not
    if current_user.role!='admin':
        flash("You are not an admin", "danger")
        return redirect('/')
    
    user= User.query.filter_by(username=username).first()
    user.role = role
    db.session.commit()
    flash(f"Succesfully set {username}'s role to {role.capitalize()}.", 'success')
    return redirect('/admin')

# Manage User's balance
@app.route('/admin/set/balance/<int:user_id>', methods=["GET", "POST"])
def set_balance(user_id):
    user = User.query.get(user_id)
    user.balance = request.form['balance']
    db.session.commit()
    flash(f"Succesfully set {user.username}'s balance to ${user.balance}.", 'success')
    return redirect('/admin')

# Admin Panel-2: For managing products

@app.route('/admin/products', methods=["GET", "POST"])
def manage_products():
    form = ProductsForm()
    products = Product.query.all()

    if form.validate_on_submit():
        product = Product(name=form.name.data, desc=form.desc.data, price=form.price.data, stock=form.stock.data, category=form.category.data)
        db.session.add(product)
        if form.img.data:
            db.session.flush() # Writes the changes to the database temporarily but does not commit them. If not flushed, product.id would be None as the id gets assinged only when it gets committed.
            filename = Utility.save_picture(form.img.data, product_id=product.id) # Retreiving the filename to save in the db.
            product.image = filename
        db.session.commit()
        flash(f'New Product: {form.name.data} added successfully.', 'success')
        return redirect('/admin/products')
    return render_template('products_dash.html', form=form, products=products)

@app.route('/admin/products/edit/<int:id>', methods=["GET", "POST"])
def update_products(id):
    product = Product.query.get(id)
    form = ProductsForm(obj=product) # Pre-poluating the form with the product's data.
    form.id = product.id # Creating an attribute called id and assigning to the form i.e instance of ProductsForm. This will help us to distinguish whether the product is being added or updated to avoid name validation issues while updating the products.

    if request.method == 'POST' and form.validate_on_submit():
        if form.img.data:
            if product.image!='default.png':
                oldFilePath = os.path.join(app.root_path, 'static', 'images', 'products', product.image)
                if os.path.exists(oldFilePath):
                    os.remove(oldFilePath)
                    filename = Utility.save_picture(form.img.data, product_id=product.id) # Retreiving the filename to save in the db.
            product.image = filename

        product.name=form.name.data
        product.desc=form.desc.data
        product.price=form.price.data
        product.stock=form.stock.data
        product.category=form.category.data
        db.session.commit()
        flash(f'Product: {form.name.data} updated successfully.', 'success')
        return redirect('/admin/products')
    return render_template('updateproduct.html', form=form, product=product)

@app.route('/admin/products/delete/<int:id>', methods=["GET", "POST"])
def delete_products(id):
    product = Product.query.get(id)
    for cart in product.carts:
        db.session.delete(cart)
    for transaction in product.transactions:
        db.session.delete(transaction)
    name = product.name
    if product.image!='default.png':
        filepath = os.path.join(app.root_path, 'static', 'images', 'products', product.image)
        os.remove(filepath)
    db.session.delete(product)
    db.session.commit()
    flash(f'Product: {name} deleted successfully.', 'success')
    return redirect('/admin/products')

# OUR WEBSITE'S VIRTUAL ECONOMY SYSTEM

@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    total = 0
    carts = current_user.carts
    transactions = current_user.transactions
    for cart in carts:
        total+=cart.amount*cart.product.price
    return render_template('cart.html', carts=carts, total=total, transactions=transactions)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    carts = current_user.carts
    if not carts:
        flash('Your cart is empty, add some items.', 'warning')
        return redirect('/')

    total = 0
    for cart in carts:
        total+=cart.amount*cart.product.price

    # If the user has insufficient balance.
    if(current_user.balance<total):
        flash(f'You need ${total-current_user.balance} more to checkout.', 'danger')
        return redirect('/cart')
    
    current_user.balance -= total
    for cart in carts:

        # Checking if user is trying to buy more than the available stocks.
        if(cart.product.stock>=cart.amount):
            # Updating the stocks.
            cart.product.stock -= cart.amount

            # Creating transaction history.
            transaction = TransactionHistory(amount=cart.amount, total=cart.product.price*cart.amount, user=current_user, product=cart.product)
            db.session.add(transaction)
            db.session.delete(cart)
        else:
            flash(f'Only {cart.product.stock} stocks left of {cart.product.name}', 'warning')
            return redirect('/cart')
    db.session.commit()
    flash('Purchase successful, thanks for shopping with us.', 'success')
    return redirect('/cart')

# To add an item in the cart or update the cart.
@app.route('/product/cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if request.method=='POST':
        cart = Cart(amount=int(request.form['quantity']), user=current_user, product=product)
        itemAlreadyCarted = [item for item in current_user.carts if item.product_id==product.id] # Checking if the user has already carted the item which they are trying to cart now.

        # We will just update the quantity of the item if the user had already carted that item before instead of adding it again in the db.
        if itemAlreadyCarted: 
            itemAlreadyCarted = itemAlreadyCarted[0]
            itemAlreadyCarted.amount = int(request.form['quantity'])
        else:
            db.session.add(cart)
        db.session.commit()
        flash(f'Product: {product.name} added to cart successfully.', 'success')

        # isRedirect helps to distinguish if the user is trying to add an item to the cart from home page or trying to update the quantity from cart page itself.
        isRedirect = request.args.get('redirect', 'true')
        if isRedirect=='true':
            return redirect('/') # If user is trying to add an item to the card from home page.
        else:
            return redirect('/cart') # If the user is trying to update the quantity from cart page itself.
    return redirect('/')

# To buy a particular item directly without adding in the cart.
@app.route('/product/buy/<int:product_id>', methods=['GET', 'POST'])
def buy_item(product_id):
    product = Product.query.get(product_id)
    quantity = int(request.form['quantity'])
    total = product.price*quantity

    # If the user has insufficient balance.
    if(current_user.balance<total):
        flash(f'You need ${total-current_user.balance} more to buy this product.', 'danger')
        return redirect('/')
    
    # If user is trying to buy more than the available stocks.
    if(product.stock<quantity):
        flash(f'Only {product.stock} stocks left of {product.name}', 'warning')
        return redirect('/')
    
    current_user.balance -= total
    product.stock -= quantity

    # Creating transaction history.
    transaction = TransactionHistory(amount=quantity, total=product.price*quantity, user=current_user, product=product)
    db.session.add(transaction)
    db.session.commit()
    flash(f'Product: {product.name} bought successfully.', 'success')
    return redirect('/')

# To remove an item in the cart.
@app.route('/product/cart/remove/<int:cart_id>', methods=['GET', 'POST'])
def remove_from_cart(cart_id):
    cart = Cart.query.get(cart_id)
    if cart:
        product = cart.product.name
        db.session.delete(cart)
        db.session.commit()
        flash(f'Product: {product} added to cart successfully.', 'success')
    else:
        flash(f'Product: {product} not found.', 'danger')
    return redirect('/cart')

# User Profile

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = ProfileForm(obj=current_user)
    return render_template('profile.html', form=form)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect('/profile')
    return render_template('editprofile.html', form=form)

# TRANSACTION HISTORY
@app.route('/transactions')
def transactions():
    transactions = current_user.transactions
    return render_template('transactionhistory.html', transactions=transactions)

if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)