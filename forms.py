import os
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, SearchField, FileField, IntegerField, SelectField
from wtforms.validators import EqualTo, DataRequired, Email, ValidationError, NumberRange
from flask_login import current_user
from models import User, Product

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    pw = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm_pw', 'Passwords do not match.')])
    confirm_pw = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('pw', 'Passwords do not match.')])
    register = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already taken.")
        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Account already registered.")
        
class PasswordResetForm(FlaskForm):
    pw = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm_pw', 'Passwords do not match.')])
    confirm_pw = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('pw', 'Passwords do not match.')])
        
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    pw = PasswordField('Password', validators=[DataRequired()])
    login = SubmitField('Sign In')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError("Invalid username.")
        
class AdminRoleSetupForm(FlaskForm):
    search = SearchField(validators=[DataRequired()])
    submit = SubmitField('Search')

class ProductsForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    desc = StringField('Product Description', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('', 'Select a category'),
        ('Food', 'Food'),
        ('Devices', 'Devices'),
        ('Games', 'Games'),
        ('Books', 'Books')
    ], validators=[DataRequired()])
    img = FileField('Product Image')
    add_product = SubmitField('Add Product')
    update_product = SubmitField('Update Product')

    def validate_name(self, name):
        product = Product.query.filter_by(name=name.data).first()
        if product and self.id!=product.id: # Second condition helps us to indentify whether the form is being used for adding a new product or updating an existing one. This prevents us from triggering the name validation if the user decide not to update the product name.
            raise ValidationError('Product already exists.')
    
    # Converting price and stock into an integer value and raising error if cannot be converted into an integer.
    def validate_price(self, price):
        try:
            price.data = int(price.data)
        except (ValueError, TypeError):
            raise ValidationError('Please specify an appropriate price.')
        
    def validate_stock(self, stock):
        try:
            stock.data = int(stock.data)
        except (ValueError, TypeError):
            raise ValidationError('Please specify an appropriate stock number.')
        
    def validate_img(self, img):
        if not img.data:
            return
        
        allowed_extensions = ['.png', '.jpg']
        ext = os.path.splitext(img.data.filename)[-1]
        if ext not in allowed_extensions:
            raise ValidationError('Unsupported file.')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[Email()])
    update = SubmitField('Update')

    def validate_username(self, username):
        if current_user.username!=username.data:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken.')
            
    def validate_email(self, email):
        if current_user.email!=email.data:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email linked with another account.')