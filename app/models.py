from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db
import hashlib, os
from datetime import datetime, timedelta
from flask import make_response, request

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    middle_name = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    role = db.relationship('Role', backref='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return self.password_hash == hashlib.md5(password.encode()).hexdigest()

    def __repr__(self):
        return '<Пользователь {}>'.format(self.login)+' <Пароль {}>'.format(self.password_hash) # Отладка

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '{}'.format(self.name) # убрать лишнее

book_genres = db.Table('book_genres',
    db.Column('book_id', db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)

class Cover(db.Model):
    __tablename__ = 'covers'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(255), nullable=False)
    md5_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Cover {self.id}>'

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publish_year = db.Column(db.Integer, nullable=False)
    publisher = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    cover_id = db.Column(db.Integer, db.ForeignKey('covers.id', ondelete='CASCADE'), nullable=False)
    genres = db.relationship('Genre', secondary=book_genres, lazy='subquery',
                             backref=db.backref('books', lazy=True))
    reviews = db.relationship('Review', backref='book', cascade='all, delete-orphan', lazy=True)
    
    def __repr__(self):
        return self

    def get_cover_url(self):
        cover = Cover.query.get(self.cover_id)
        return cover.file_name if cover else None

    def delete_cover_file(self):
        cover = Cover.query.filter(Cover.id == self.cover_id).first()
        print('self', self.cover_id)
        print('db_cover', cover)
        if cover:
            file_path = os.path.join('app/static/covers/', cover.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(cover)
            db.session.commit()

    def check_user_reviewed(self, req_user_id):
        reviews_of_book = Review.query.filter_by(book_id = self.id, user_id = req_user_id).first()
        if reviews_of_book is None:
            return False
        else:
            return True
    
    def get_rating_info(self):
        book_ratings = Review.query.filter_by(book_id = self.id).all()
        rating_count = len(book_ratings)

        if rating_count == 0:
                return False
        else:
            avg_rating = 0
            for book_rating in book_ratings:
                avg_rating += book_rating.rating
            avg_rating = round(avg_rating / rating_count, 1)
            output = {'rating_count': rating_count, 'avg_rating': avg_rating}
            return output

class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return self.name

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.TIMESTAMP, server_default=db.func.now(), nullable=False)

    def __repr__(self):
        return self

class UserView(db.Model):
    __tablename__ = 'user_views'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    view_date = db.Column(db.TIMESTAMP, server_default=db.func.now(), nullable=False)

    user = db.relationship('User', backref='views')
    book = db.relationship('Book', backref='views')

    def __repr__(self):
        return str(self)

    def add_book_view(user_id, book_id):
        # текущее время
        today_start = datetime.combine(datetime.today(), datetime.min.time())
        today_end = today_start + timedelta(days=1)

        # все просмотры пользователя за день
        view_count = UserView.query.filter(
            UserView.user_id == user_id,
            UserView.book_id == book_id,
            UserView.view_date >= today_start,
            UserView.view_date < today_end
        ).count()

        if view_count < 10:
            new_view = UserView(user_id=user_id, book_id=book_id)
            db.session.add(new_view)
            db.session.commit()