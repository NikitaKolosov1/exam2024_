def log_user_view(book_id):
    
    user_id = current_user.id if current_user.is_authenticated else None

    today = datetime.utcnow().date()
    start_of_today = datetime(today.year, today.month, today.day)
    end_of_today = start_of_today + timedelta(days=1)

    today_views = UserView.query.filter(
        UserView.session_id == session_id,
        UserView.book_id == book_id,
        UserView.view_date >= start_of_today,
        UserView.view_date < end_of_today
    ).count()

    if today_views >= 10:
        return False
    pass