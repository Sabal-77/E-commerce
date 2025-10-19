from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(1000), nullable=False)
    role = db.Column(db.String(1000), default='user')
    balance = db.Column(db.Integer, default=10000)

    # One to many relationships
    carts = db.relationship('Cart', backref='user')
    transactions = db.relationship('TransactionHistory', backref='user')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    desc = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(32), nullable=False)
    image = db.Column(db.String(32), default='default.png')

    # One to many relationships
    carts = db.relationship('Cart', backref='product')
    transactions = db.relationship('TransactionHistory', backref='product')

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    amount = db.Column(db.Integer, default=1)

class TransactionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_transactionhistory_user'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', name='fk_transactionhistory_product'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)