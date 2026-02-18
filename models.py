from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Role(db.Model):
    __tablename__ = 'role'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(100), unique=True, nullable=False)

    users = db.relationship('User', backref='role', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    user_surname = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_patronymic = db.Column(db.String(100), nullable=False)
    user_login = db.Column(db.Text, nullable=False)
    user_password = db.Column(db.Text, nullable=False)
    user_role = db.Column(db.Integer, db.ForeignKey('role.role_id'), nullable=False)

    def get_id(self):
        return str(self.user_id)

    @property
    def full_name(self):
        return f"{self.user_surname} {self.user_name} {self.user_patronymic}"

    @property
    def is_admin(self):
        return self.user_role == 1

    @property
    def is_manager(self):
        return self.user_role == 2

    @property
    def is_client(self):
        return self.user_role == 3


class Manufacturer(db.Model):
    __tablename__ = 'manufacturer'
    manufacturer_id = db.Column(db.Integer, primary_key=True)
    manufacturer_name = db.Column(db.String(200), unique=True, nullable=False)

    products = db.relationship('Product', backref='manufacturer', lazy=True)


class Supplier(db.Model):
    __tablename__ = 'supplier'
    supplier_id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(200), unique=True, nullable=False)

    products = db.relationship('Product', backref='supplier', lazy=True)


class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(200), unique=True, nullable=False)

    products = db.relationship('Product', backref='category', lazy=True)


class UnitOfMeasure(db.Model):
    __tablename__ = 'unit_of_measure'
    unit_id = db.Column(db.Integer, primary_key=True)
    unit_name = db.Column(db.String(50), unique=True, nullable=False)
    unit_short_name = db.Column(db.String(20), nullable=False)

    products = db.relationship('Product', backref='unit', lazy=True)


class Product(db.Model):
    __tablename__ = 'product'
    product_article_number = db.Column(db.String(100), primary_key=True)
    product_type = db.Column(db.String(200), nullable=False)
    product_model = db.Column(db.Text, nullable=False)
    product_description = db.Column(db.Text, nullable=False)
    product_unit = db.Column(db.Integer, db.ForeignKey('unit_of_measure.unit_id'), nullable=False)
    product_category = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    product_photo = db.Column(db.String(500), nullable=True)
    product_manufacturer = db.Column(db.Integer, db.ForeignKey('manufacturer.manufacturer_id'), nullable=False)
    product_supplier = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'), nullable=False)
    product_cost = db.Column(db.Numeric(19, 4), nullable=False)
    product_max_discount = db.Column(db.SmallInteger, nullable=False)
    product_current_discount = db.Column(db.SmallInteger, nullable=False)
    product_quantity_in_stock = db.Column(db.Integer, nullable=False)
    product_status = db.Column(db.String(50), nullable=False, default='В наличии')

    order_products = db.relationship('OrderProduct', backref='product', lazy=True)

    @property
    def discounted_price(self):
        return float(self.product_cost) * (1 - self.product_current_discount / 100)

    @property
    def display_name(self):
        return f"{self.product_type} {self.product_model}"


class PickupPoint(db.Model):
    __tablename__ = 'pickup_point'
    pickup_point_id = db.Column(db.Integer, primary_key=True)
    pickup_point_address = db.Column(db.Text, unique=True, nullable=False)

    orders = db.relationship('Order', backref='pickup_point', lazy=True)


class OrderStatus(db.Model):
    __tablename__ = 'order_status'
    order_status_id = db.Column(db.Integer, primary_key=True)
    order_status_name = db.Column(db.String(50), unique=True, nullable=False)

    orders = db.relationship('Order', backref='status', lazy=True)


class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    customer_surname = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_patronymic = db.Column(db.String(100), nullable=False)
    customer_code = db.Column(db.Integer, unique=True, nullable=False)

    orders = db.relationship('Order', backref='customer', lazy=True)

    @property
    def full_name(self):
        return f"{self.customer_surname} {self.customer_name} {self.customer_patronymic}"


class Order(db.Model):
    __tablename__ = 'order'
    order_id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    order_delivery_date = db.Column(db.DateTime, nullable=False)
    order_pickup_point = db.Column(db.Integer, db.ForeignKey('pickup_point.pickup_point_id'), nullable=False)
    order_customer = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=True)
    order_pickup_code = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.Integer, db.ForeignKey('order_status.order_status_id'), nullable=False)

    order_products = db.relationship('OrderProduct', backref='order', lazy=True, cascade='all, delete-orphan')

    @property
    def total_cost(self):
        return sum(op.product.discounted_price * op.product_quantity for op in self.order_products)

    @property
    def total_quantity(self):
        return sum(op.product_quantity for op in self.order_products)


class OrderProduct(db.Model):
    __tablename__ = 'order_product'
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), primary_key=True)
    product_article_number = db.Column(db.String(100), db.ForeignKey('product.product_article_number'),
                                       primary_key=True)
    product_quantity = db.Column(db.Integer, nullable=False)