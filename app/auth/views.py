from flask import render_template, redirect, url_for, flash, request, make_response
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.auth import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        user = User.query.filter_by(login=username).first()
        if user and user.check_password(password): 
            login_user(user, remember=remember_me)
            flash('Вы успешно вошли в систему.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    response = make_response(redirect(url_for('main.index')))
    response.delete_cookie('viewed_books') # убрать, чтобы сохранять просмотренные книги всегда
    return response
