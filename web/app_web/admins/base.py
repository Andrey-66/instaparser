from flask import flash, redirect, url_for, request
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

class BaseAdminView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        flash('Нет прав доступа к этому разделу', 'error')
        return redirect(url_for('admin.index'))