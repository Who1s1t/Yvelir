import osssss
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import random

from config import Config
from models import db, User, Role, Product, Manufacturer, Supplier, Category, UnitOfMeasure
from models import PickupPoint, OrderStatus, Customer, Order, OrderProduct
from forms import LoginForm, ProductForm, OrderForm, SearchForm

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, авторизуйтесь для доступа к этой странице.'

# Настройка загрузки файлов
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
ALLOWED_EXTENSIONS = app.config['ALLOWED_EXTENSIONS']
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def utility_processor():
    return {
        'now': datetime.now(),
        'UserRole': {
            'GUEST': 0,
            'ADMIN': 1,
            'MANAGER': 2,
            'CLIENT': 3
        }
    }


# ==================== ГЛАВНАЯ И АВТОРИЗАЦИЯ ====================

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('products'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_login=form.login.data).first()
        if user and user.user_password == form.password.data:
            login_user(user)
            flash(f'Добро пожаловать, {user.full_name}!', 'success')
            return redirect(url_for('products'))
        else:
            flash('Неверный логин или пароль', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('products'))


@app.route('/guest')
def guest_login():
    logout_user()
    flash('Вы вошли как гость', 'info')
    return redirect(url_for('products'))


# ==================== ТОВАРЫ ====================

@app.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('PRODUCTS_PER_PAGE', 20)

    query = Product.query.join(Manufacturer).join(Category).join(UnitOfMeasure)

    # Поиск и фильтрация для менеджера и админа
    if current_user.is_authenticated and (current_user.is_admin or current_user.is_manager):
        form = SearchForm()
        form.manufacturer.choices = [(0, 'Все производители')] + [(m.manufacturer_id, m.manufacturer_name) for m in
                                                                  Manufacturer.query.all()]
        form.category.choices = [(0, 'Все категории')] + [(c.category_id, c.category_name) for c in
                                                          Category.query.all()]

        search = request.args.get('search', '')
        manufacturer_id = request.args.get('manufacturer', 0, type=int)
        category_id = request.args.get('category', 0, type=int)
        sort = request.args.get('sort', 'name_asc')

        if search:
            query = query.filter(
                db.or_(
                    Product.product_type.ilike(f'%{search}%'),
                    Product.product_model.ilike(f'%{search}%'),
                    Product.product_description.ilike(f'%{search}%'),
                    Product.product_article_number.ilike(f'%{search}%')
                )
            )

        if manufacturer_id > 0:
            query = query.filter(Product.product_manufacturer == manufacturer_id)

        if category_id > 0:
            query = query.filter(Product.product_category == category_id)

        # Сортировка
        if sort == 'name_asc':
            query = query.order_by(Product.product_type, Product.product_model)
        elif sort == 'name_desc':
            query = query.order_by(Product.product_type.desc(), Product.product_model.desc())
        elif sort == 'cost_asc':
            query = query.order_by(Product.product_cost)
        elif sort == 'cost_desc':
            query = query.order_by(Product.product_cost.desc())
        elif sort == 'discount_asc':
            query = query.order_by(Product.product_current_discount)
        elif sort == 'discount_desc':
            query = query.order_by(Product.product_current_discount.desc())
    else:
        form = None
        search = ''
        manufacturer_id = 0
        category_id = 0
        sort = 'name_asc'

    products = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('products.html',
                           products=products,
                           form=form,
                           search=search,
                           manufacturer_id=manufacturer_id,
                           category_id=category_id,
                           sort=sort)


@app.route('/product/<article>')
def product_detail(article):
    product = Product.query.get_or_404(article)
    return render_template('product_detail.html', product=product)


@app.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not (current_user.is_admin or current_user.is_manager):
        flash('У вас нет прав для добавления товаров', 'danger')
        return redirect(url_for('products'))

    form = ProductForm()
    form.unit.choices = [(u.unit_id, f"{u.unit_name} ({u.unit_short_name})") for u in UnitOfMeasure.query.all()]
    form.category.choices = [(c.category_id, c.category_name) for c in Category.query.all()]
    form.manufacturer.choices = [(m.manufacturer_id, m.manufacturer_name) for m in Manufacturer.query.all()]
    form.supplier.choices = [(s.supplier_id, s.supplier_name) for s in Supplier.query.all()]

    if form.validate_on_submit():
        # Проверяем, существует ли уже товар с таким артикулом
        existing_product = Product.query.get(form.article.data)
        if existing_product:
            flash('Товар с таким артикулом уже существует', 'danger')
            return render_template('product_form.html', form=form, title='Добавление товара')

        product = Product(
            product_article_number=form.article.data,
            product_type=form.product_type.data,
            product_model=form.model.data,
            product_description=form.description.data,
            product_unit=form.unit.data,
            product_category=form.category.data,
            product_manufacturer=form.manufacturer.data,
            product_supplier=form.supplier.data,
            product_cost=form.cost.data,
            product_max_discount=form.max_discount.data,
            product_current_discount=form.current_discount.data,
            product_quantity_in_stock=form.quantity.data,
            product_status=form.status.data
        )

        # Обработка фото
        if form.photo.data:
            file = form.photo.data
            if file and allowed_file(file.filename):
                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{form.article.data}.{extension}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.product_photo = filename

        try:
            db.session.add(product)
            db.session.commit()
            flash('Товар успешно добавлен', 'success')
            return redirect(url_for('product_detail', article=product.product_article_number))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении товара: {str(e)}', 'danger')

    return render_template('product_form.html', form=form, title='Добавление товара')


@app.route('/product/<article>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(article):
    if not (current_user.is_admin or current_user.is_manager):
        flash('У вас нет прав для редактирования товаров', 'danger')
        return redirect(url_for('products'))

    product = Product.query.get_or_404(article)
    form = ProductForm()
    form.unit.choices = [(u.unit_id, f"{u.unit_name} ({u.unit_short_name})") for u in UnitOfMeasure.query.all()]
    form.category.choices = [(c.category_id, c.category_name) for c in Category.query.all()]
    form.manufacturer.choices = [(m.manufacturer_id, m.manufacturer_name) for m in Manufacturer.query.all()]
    form.supplier.choices = [(s.supplier_id, s.supplier_name) for s in Supplier.query.all()]

    if form.validate_on_submit():
        product.product_type = form.product_type.data
        product.product_model = form.model.data
        product.product_description = form.description.data
        product.product_unit = form.unit.data
        product.product_category = form.category.data
        product.product_manufacturer = form.manufacturer.data
        product.product_supplier = form.supplier.data
        product.product_cost = form.cost.data
        product.product_max_discount = form.max_discount.data
        product.product_current_discount = form.current_discount.data
        product.product_quantity_in_stock = form.quantity.data
        product.product_status = form.status.data

        # Обработка фото
        if form.photo.data:
            file = form.photo.data
            if file and allowed_file(file.filename):
                # Удаляем старое фото
                if product.product_photo:
                    old_file = os.path.join(app.config['UPLOAD_FOLDER'], product.product_photo)
                    if os.path.exists(old_file):
                        os.remove(old_file)

                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{article}.{extension}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.product_photo = filename

        try:
            db.session.commit()
            flash('Товар успешно обновлен', 'success')
            return redirect(url_for('product_detail', article=product.product_article_number))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении товара: {str(e)}', 'danger')

    elif request.method == 'GET':
        form.article.data = product.product_article_number
        form.product_type.data = product.product_type
        form.model.data = product.product_model
        form.description.data = product.product_description
        form.unit.data = product.product_unit
        form.category.data = product.product_category
        form.manufacturer.data = product.product_manufacturer
        form.supplier.data = product.product_supplier
        form.cost.data = float(product.product_cost)
        form.max_discount.data = product.product_max_discount
        form.current_discount.data = product.product_current_discount
        form.quantity.data = product.product_quantity_in_stock
        form.status.data = product.product_status

    return render_template('product_form.html', form=form, title='Редактирование товара', product=product)


@app.route('/product/<article>/delete', methods=['POST'])
@login_required
def delete_product(article):
    if not current_user.is_admin:
        flash('Только администратор может удалять товары', 'danger')
        return redirect(url_for('products'))

    product = Product.query.get_or_404(article)

    # Проверяем, есть ли заказы с этим товаром
    if product.order_products:
        flash('Нельзя удалить товар, который есть в заказах', 'danger')
        return redirect(url_for('product_detail', article=article))

    try:
        # Удаляем фото
        if product.product_photo:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], product.product_photo)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(product)
        db.session.commit()
        flash('Товар успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении товара: {str(e)}', 'danger')

    return redirect(url_for('products'))


# ==================== ЗАКАЗЫ ====================

@app.route('/orders')
@login_required
def orders():
    if not (current_user.is_admin or current_user.is_manager):
        flash('У вас нет прав для просмотра заказов', 'danger')
        return redirect(url_for('products'))

    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ORDERS_PER_PAGE', 15)

    query = Order.query.join(OrderStatus).join(PickupPoint).outerjoin(Customer)
    query = query.order_by(Order.order_date.desc())

    orders = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('orders.html', orders=orders)


@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    if not (current_user.is_admin or current_user.is_manager):
        flash('У вас нет прав для просмотра заказов', 'danger')
        return redirect(url_for('products'))

    order = Order.query.get_or_404(order_id)
    return render_template('order_detail.html', order=order)


@app.route('/order/add', methods=['GET', 'POST'])
@login_required
def add_order():
    if not (current_user.is_admin or current_user.is_manager):
        flash('У вас нет прав для создания заказов', 'danger')
        return redirect(url_for('products'))

    form = OrderForm()
    form.pickup_point.choices = [(p.pickup_point_id, p.pickup_point_address) for p in PickupPoint.query.all()]
    form.customer.choices = [(0, 'Без клиента')] + [(c.customer_id, c.full_name) for c in Customer.query.all()]
    form.status.choices = [(s.order_status_id, s.order_status_name) for s in OrderStatus.query.all()]

    if form.validate_on_submit():
        # Генерируем код для получения
        pickup_code = random.randint(100, 999)

        order = Order(
            order_date=datetime.now(),
            order_delivery_date=datetime.combine(form.delivery_date.data, datetime.min.time()),
            order_pickup_point=form.pickup_point.data,
            order_customer=form.customer.data if form.customer.data > 0 else None,
            order_pickup_code=pickup_code,
            order_status=form.status.data
        )

        try:
            db.session.add(order)
            db.session.commit()
            flash('Заказ успешно создан', 'success')
            return redirect(url_for('edit_order', order_id=order.order_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании заказа: {str(e)}', 'danger')

    return render_template('order_form.html', form=form, title='Создание заказа')


@app.route('/order/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    if not (current_user.is_admin or current_user.is_manager):
        flash('У вас нет прав для редактирования заказов', 'danger')
        return redirect(url_for('products'))

    order = Order.query.get_or_404(order_id)
    form = OrderForm()
    form.pickup_point.choices = [(p.pickup_point_id, p.pickup_point_address) for p in PickupPoint.query.all()]
    form.customer.choices = [(0, 'Без клиента')] + [(c.customer_id, c.full_name) for c in Customer.query.all()]
    form.status.choices = [(s.order_status_id, s.order_status_name) for s in OrderStatus.query.all()]

    if form.validate_on_submit():
        order.order_delivery_date = datetime.combine(form.delivery_date.data, datetime.min.time())
        order.order_pickup_point = form.pickup_point.data
        order.order_customer = form.customer.data if form.customer.data > 0 else None
        order.order_status = form.status.data

        try:
            db.session.commit()
            flash('Заказ успешно обновлен', 'success')
            return redirect(url_for('order_detail', order_id=order.order_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении заказа: {str(e)}', 'danger')

    elif request.method == 'GET':
        form.delivery_date.data = order.order_delivery_date.date()
        form.pickup_point.data = order.order_pickup_point
        form.customer.data = order.order_customer if order.order_customer else 0
        form.status.data = order.order_status

    # Получаем товары для добавления
    products = Product.query.filter(Product.product_quantity_in_stock > 0).all()

    return render_template('order_form.html',
                           form=form,
                           title='Редактирование заказа',
                           order=order,
                           products=products)


@app.route('/order/<int:order_id>/add_product', methods=['POST'])
@login_required
def add_order_product(order_id):
    if not (current_user.is_admin or current_user.is_manager):
        return jsonify({'error': 'Нет прав'}), 403

    order = Order.query.get_or_404(order_id)

    data = request.get_json()
    article = data.get('article')
    quantity = int(data.get('quantity', 1))

    product = Product.query.get_or_404(article)

    # Проверяем наличие на складе
    if product.product_quantity_in_stock < quantity:
        return jsonify({'error': f'Недостаточно товара на складе. В наличии: {product.product_quantity_in_stock}'}), 400

    # Проверяем, есть ли уже такой товар в заказе
    order_product = OrderProduct.query.filter_by(
        order_id=order_id,
        product_article_number=article
    ).first()

    if order_product:
        order_product.product_quantity += quantity
    else:
        order_product = OrderProduct(
            order_id=order_id,
            product_article_number=article,
            product_quantity=quantity
        )
        db.session.add(order_product)

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'product': {
                'article': product.product_article_number,
                'name': product.display_name,
                'quantity': order_product.product_quantity,
                'price': float(product.discounted_price),
                'total': float(product.discounted_price * order_product.product_quantity)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/order/<int:order_id>/update_product', methods=['POST'])
@login_required
def update_order_product(order_id):
    if not (current_user.is_admin or current_user.is_manager):
        return jsonify({'error': 'Нет прав'}), 403

    data = request.get_json()
    article = data.get('article')
    quantity = int(data.get('quantity', 1))

    order_product = OrderProduct.query.filter_by(
        order_id=order_id,
        product_article_number=article
    ).first_or_404()

    product = Product.query.get_or_404(article)

    # Проверяем наличие на складе
    if product.product_quantity_in_stock < quantity:
        return jsonify({'error': f'Недостаточно товара на складе. В наличии: {product.product_quantity_in_stock}'}), 400

    order_product.product_quantity = quantity

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'quantity': quantity,
            'total': float(product.discounted_price * quantity)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/order/<int:order_id>/remove_product/<article>', methods=['POST'])
@login_required
def remove_order_product(order_id, article):
    if not (current_user.is_admin or current_user.is_manager):
        return jsonify({'error': 'Нет прав'}), 403

    order_product = OrderProduct.query.filter_by(
        order_id=order_id,
        product_article_number=article
    ).first_or_404()

    try:
        db.session.delete(order_product)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/order/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    if not current_user.is_admin:
        flash('Только администратор может удалять заказы', 'danger')
        return redirect(url_for('orders'))

    order = Order.query.get_or_404(order_id)

    try:
        db.session.delete(order)
        db.session.commit()
        flash('Заказ успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении заказа: {str(e)}', 'danger')

    return redirect(url_for('orders'))


# ==================== ПУНКТЫ ВЫДАЧИ ====================

@app.route('/pickup-points')
@login_required
def pickup_points():
    if not current_user.is_admin:
        flash('У вас нет прав для просмотра пунктов выдачи', 'danger')
        return redirect(url_for('products'))

    points = PickupPoint.query.all()
    return render_template('pickup_points.html', points=points)


# ==================== СТАТИСТИКА ====================

@app.route('/stats')
@login_required
def statistics():
    if not current_user.is_admin:
        flash('У вас нет прав для просмотра статистики', 'danger')
        return redirect(url_for('products'))

    # Общая статистика
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = Customer.query.count()
    total_manufacturers = Manufacturer.query.count()

    # Товары с низким запасом
    low_stock_products = Product.query.filter(Product.product_quantity_in_stock < 5).count()

    # Заказы по статусам
    orders_by_status = db.session.query(
        OrderStatus.order_status_name,
        db.func.count(Order.order_id)
    ).join(Order).group_by(OrderStatus.order_status_name).all()

    # Товары по категориям
    products_by_category = db.session.query(
        Category.category_name,
        db.func.count(Product.product_article_number)
    ).join(Product).group_by(Category.category_name).all()

    return render_template('stats.html',
                           total_products=total_products,
                           total_orders=total_orders,
                           total_customers=total_customers,
                           total_manufacturers=total_manufacturers,
                           low_stock_products=low_stock_products,
                           orders_by_status=orders_by_status,
                           products_by_category=products_by_category)


# ==================== СТАТИКА ====================

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
