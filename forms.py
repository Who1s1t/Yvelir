from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, FloatField, TextAreaField, DateField, FileField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class ProductForm(FlaskForm):
    article = StringField('Артикул', validators=[DataRequired(), Length(max=100)])
    product_type = StringField('Тип изделия', validators=[DataRequired(), Length(max=200)])
    model = StringField('Модель', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    unit = SelectField('Единица измерения', coerce=int, validators=[DataRequired()])
    category = SelectField('Категория', coerce=int, validators=[DataRequired()])
    manufacturer = SelectField('Производитель', coerce=int, validators=[DataRequired()])
    supplier = SelectField('Поставщик', coerce=int, validators=[DataRequired()])
    cost = FloatField('Цена', validators=[DataRequired(), NumberRange(min=0)])
    max_discount = IntegerField('Макс. скидка %', validators=[DataRequired(), NumberRange(min=0, max=100)])
    current_discount = IntegerField('Тек. скидка %', validators=[DataRequired(), NumberRange(min=0, max=100)])
    quantity = IntegerField('Количество', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Статус', choices=[('В наличии', 'В наличии'), ('Нет в наличии', 'Нет в наличии'), ('Под заказ', 'Под заказ')])
    photo = FileField('Фото', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')])
    submit = SubmitField('Сохранить')

class OrderForm(FlaskForm):
    delivery_date = DateFiфывыфвыфeld('Дата доставки', validators=[DataRequired()], format='%Y-%m-%d')
    pickup_point = SelectField('Пункт выдачи', coerce=int, validators=[DataRequired()])
    customer = SelectField('Клиент', coerce=int, validators=[Optional()])
    status = SelectField('Статус', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Сохранить')

class SearchForm(FlaskForm):
    search = StringField('Поиск', validators=[Optional()])
    manufacturer = SelectField('Производитель', coerce=int, validators=[Optional()])
    category = SelectField('Категория', coerce=int, validators=[Optional()])
    sort = SelectField('Сортировка', choices=[
        ('name_asc', 'Название (А-Я)'),
        ('name_desc', 'Название (Я-А)'),
        ('cost_asc', 'Цена (по возрастанию)'),
        ('cost_desc', 'Цена (по убыванию)'),
        ('discount_asc', 'Скидка (по возрастанию)'),
        ('discount_desc', 'Скидка (по убыванию)')
    ], validators=[Optional()])
    submit = SubmitField('Применить')