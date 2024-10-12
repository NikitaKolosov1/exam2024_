from flask import render_template, request, redirect, url_for, flash, make_response
from flask_login import current_user, login_required
from app.main import main_bp
import os, hashlib
import bleach
from app.models import Genre, Cover, Book, User, Review, UserView
from app import db
import json
from datetime import datetime, timedelta
from sqlalchemy import func

@main_bp.route('/index')
@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 9

    all_books = Book.query.order_by(Book.id.desc()).all()
    
    total_views = len(all_books)
    total_pages = (total_views + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    paginated_books = all_books[start:end]

    page_range = range(max(1, page - 2), min(total_pages + 1, page + 3))

    reviews = Review.query.all()

    #недавно просмотренные книги
    viewed_books_cookie = request.cookies.get('viewed_books')
    if viewed_books_cookie:
        viewed_books_list = json.loads(viewed_books_cookie)

        recent_books = Book.query.filter(Book.id.in_(viewed_books_list)).all()

        recent_books.sort(key=lambda x: viewed_books_list.index(x.id))
    else:
        recent_books = []

    #популярные книги
    three_months_ago = datetime.now() - timedelta(days=90)
    popular_books = (db.session.query(Book)
                     .join(UserView, UserView.book_id == Book.id)
                     .filter(UserView.view_date >= three_months_ago)
                     .group_by(Book.id)
                     .order_by(db.func.count(UserView.id).desc())
                     .limit(5)
                     .all())
        
    return render_template('index.html', title='Список книг', books=paginated_books, page=page, total_pages=total_pages, recent_books=recent_books, popular_books=popular_books)


@main_bp.route('/addbook', methods=['GET', 'POST'])
def addbook():
    if(current_user.is_authenticated == False):
        print(current_user.is_authenticated)
        flash('Для выполнения данного действия необходимо пройти процедуру аутентификации','danger')
        return redirect(url_for('main.index'))
    if(current_user.is_authenticated == True and str(current_user.role) != 'Администратор'):
        flash('Для выполнения данного действия необходимо иметь другие права','danger')
        return redirect(url_for('main.index'))

    genres = Genre.query.order_by(Genre.id).all()
    if request.method == 'POST':
        title = request.form['title']
        description = bleach.clean(request.form['description'])
        year = request.form['year']
        publisher = request.form['publisher']
        author = request.form['author']
        pages = request.form['pages']
        genres = request.form.getlist('genres')
        input_cover_file = request.files['cover']

        try:
            if input_cover_file:
                file_extenstion = input_cover_file.filename.split('.')[-1].lower()
                mime_type = input_cover_file.mimetype
                md5_hash = hashlib.md5(input_cover_file.read()).hexdigest()

                cover = Cover.query.filter_by(md5_hash=md5_hash).first()
                if not cover:
                    lastest_id_cover = Cover.query.order_by(Cover.id.desc()).first().id
                    if lastest_id_cover:
                        new_filename = str(lastest_id_cover + 1) + '.' + file_extenstion
                    else:
                        new_filename = '1' + '.' + file_extenstion #если в базе нет записей

                    cover_path = os.path.join('app/static/covers/', new_filename)
                    input_cover_file.seek(0)
                    with open(str(cover_path), mode="wb") as file:
                        contents = file.write(input_cover_file.read())

                    cover = Cover(file_name=new_filename, mime_type=mime_type, md5_hash=md5_hash)
                    db.session.add(cover)
                    db.session.commit()

                new_book = Book(
                    title=title,
                    description=description,
                    publish_year=year,
                    publisher=publisher,
                    author=author,
                    pages=pages,
                    cover_id=cover.id
                )
            db.session.add(new_book)
            db.session.commit()

            for genre_id in genres:
                genre = Genre.query.get(genre_id)
                new_book.genres.append(genre)
            db.session.commit()
            
            return redirect(url_for('main.index'))

        except Exception as e:
            print(e)
            flash('Ошибка добавления в базу данных ', 'danger')
            db.session.rollback()
            return redirect(url_for('main.index'))
        
    else: # get метод
        return render_template('add_book.html', title='Добавить книгу', genres=genres)

@main_bp.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    print(book.title)
    if book.id is None:
        return redirect(url_for('main.index'))

    if (current_user.is_authenticated == True):
        UserView.add_book_view(user_id=current_user.id, book_id=book_id)
    
    viewed_books_cookie = request.cookies.get('viewed_books')
    if viewed_books_cookie:
        viewed_books_list = json.loads(viewed_books_cookie)
    else:
        viewed_books_list = []

    if book_id in viewed_books_list:
        viewed_books_list.remove(book_id)
    viewed_books_list.insert(0, book_id)
    if len(viewed_books_list) > 5:
        viewed_books_list = viewed_books_list[:5]

    response = make_response(render_template('book_detail.html', book=book))
    response.set_cookie('viewed_books', json.dumps(viewed_books_list), max_age=30*24*60*60) 
    return response

@main_bp.route('/editbook', methods =['GET','POST'])
def edit_book():
    if(current_user.is_authenticated == False):
        print(current_user.is_authenticated)
        flash('Для выполнения данного действия необходимо пройти процедуру аутентификации','danger')
        return redirect(url_for('main.index'))
    if(current_user.is_authenticated == True and str(current_user.role) == 'Пользователь'):
        flash('Для выполнения данного действия необходимо иметь другие права','danger')
        return redirect(url_for('main.index'))

    book_id = ''
    if request.method == 'POST':
        book_id = request.form.get('selected_book')
    else: 
        book_id = request.args.get('book_id')
    if not book_id:
        print('Не передан id книги')
        return redirect(url_for('main.index'))
    
    book = Book.query.get(book_id)
    if not book:
        print('Нет такой книги')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        try:
            book.title = request.form['title']
            book.description = bleach.clean(request.form['description_area'])
            book.publish_year = request.form['year']
            book.publisher = request.form['publisher']
            book.author = request.form['author']
            book.pages = request.form['pages']
            genres = request.form.getlist('genres')

            book.genres = []
            for genre_id in genres:
                genre = Genre.query.get(genre_id)
                book.genres.append(genre)
            db.session.commit()
            flash('Книга успешно отредактирована','success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            print(e)
            flash('Ошибка при сохранении', 'danger')
            return redirect(url_for('main.index'))

    return render_template('edit_book.html', book=book, all_genres=Genre.query.all())

@main_bp.route('/deletebook/<int:book_id>')
def delete_book(book_id):
    if(current_user.is_authenticated == False):
        print(current_user.is_authenticated)
        flash('Для выполнения данного действия необходимо пройти процедуру аутентификации','danger')
        return redirect(url_for('main.index'))
    if(current_user.is_authenticated == True and str(current_user.role) != 'Администратор'):
        flash('Для выполнения данного действия необходимо иметь другие права','danger')
        return redirect(url_for('main.index'))

    book = Book.query.get_or_404(book_id)
    try:
        db.session.delete(book)
        db.session.commit()
        book.delete_cover_file()
        flash('Книга успешно удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash('Ошибка при удалении книги.', 'danger')
    return redirect(url_for('main.index'))

@main_bp.route('/review', methods=['GET', 'POST'])
def review():
    
    if(current_user.is_authenticated == False):
        print(current_user.is_authenticated)
        flash('Для выполнения данного действия необходимо пройти процедуру аутентификации','danger')
        return redirect(url_for('main.index'))
        
    mode = request.args.get('mode', 'edit')

    if request.method == 'POST' and mode == 'edit':
        try:
            review_content = bleach.clean(request.form.get('review'))
            rating = int(request.form.get('rating'))
            user_id = current_user.id
            book_id = int(request.form.get('book_id'))

            existing_review = Review.query.filter_by(user_id=user_id, book_id=book_id).first()
            if existing_review:
                flash('Вы уже оставляли рецензию на эту книгу.', 'warning')
                return redirect(url_for('main.index'))

            new_review = Review(
            book_id=book_id,
            user_id=user_id,
            rating=rating,
            review_text=review_content
            )

            db.session.add(new_review)
            db.session.commit()

            flash('Отзыв успешно сохранён!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Ошибка при создании отзыва', 'danger')

    else:
        req_book_id = request.args.get('book_id')
        review = Review.query.filter_by(book_id=req_book_id, user_id=current_user.id).first()
        return render_template('review.html', mode=mode, review=review)
    return render_template('review.html')


@main_bp.route('/statistic', methods=['GET', 'POST'])
def statistic():
    if(current_user.is_authenticated == False):
        print(current_user.is_authenticated)
        flash('Для выполнения данного действия необходимо пройти процедуру аутентификации','danger')
        return redirect(url_for('main.index'))
    if(current_user.is_authenticated == True and str(current_user.role) != 'Администратор'):
        flash('Для выполнения данного действия необходимо иметь другие права','danger')
        return redirect(url_for('main.index'))

    per_page = 10
    
    user_views = UserView.query.order_by(UserView.view_date.desc()).all()
    user_views_page = request.args.get('user_views_page', 1, type=int) # текущая страница    
    user_total_pages = (len(user_views) + per_page - 1) // per_page # всего страниц
    start = (user_views_page - 1) * per_page
    end = start + per_page
    paginated_users = user_views[start:end]

    book_stats_page = 1
    book_total_pages = 1
    if request.method == 'POST':
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')

        if (date_from is not None) and (date_to is not None):
            book_stats = db.session.query(Book.title, func.count(UserView.id).label('view_count')) \
                       .join(UserView, UserView.book_id == Book.id) \
                       .filter(UserView.user_id != None) \
                       .filter(UserView.view_date.between(date_from, date_to)) \
                       .group_by(Book.id) \
                       .order_by(func.count(UserView.id).desc())
            
            all_books = Book.query.order_by(Book.id.desc()).all()
            book_stats_page = request.args.get('book_stats_page', 1, type=int) #текущая старница
            book_total_pages = (len(all_books) + per_page - 1) // per_page # всего страниц
            start = (book_total_pages - 1) * per_page
            end = start + per_page
            paginated_books = book_stats[start:end]
        return render_template('statistic.html', paginated_books=paginated_books, \
        book_stats_page=book_stats_page, book_total_pages=book_total_pages, \
            user_views_page=user_views_page, user_total_pages=user_total_pages, paginated_users=paginated_users)

    
    #user_views - все записи из бд
    #user_total_pages - сколько всего страниц записей у действий пользователя
    #user_current_page - выбранная страница пользователя
    return render_template('statistic.html', \
        user_views_page=user_views_page, user_total_pages=user_total_pages, paginated_users=paginated_users,\
            book_stats_page=book_stats_page, book_total_pages=book_total_pages)

    