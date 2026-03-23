from flask import flash, redirect, url_for, request
from flask_login import current_user

from app_web import Post

from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import FilterEqual, BooleanEqualFilter, DateEqualFilter


class PostAdminView(ModelView):
    column_list = ('id', 'instagram_post_id', 'profile_id', 'profile', 'media_type',
                   'is_sent', 'sent_at', 'sent_to', 'is_downloaded',
                   'file_path', 'created_at', 'errors_count')
    column_searchable_list = ('instagram_post_id', 'sent_to', 'file_path')
    column_default_sort = ('created_at', True)  # True = descending
    column_filters = [
        FilterEqual(Post.instagram_post_id, 'Instagram Post ID'),
        FilterEqual(Post.profile_id, 'Profile ID'),
        FilterEqual(Post.media_type, 'Media Type'),
        BooleanEqualFilter(Post.is_sent, 'Is Sent'),
        BooleanEqualFilter(Post.is_downloaded, 'Is Downloaded'),
        FilterEqual(Post.errors_count, 'Errors Count'),
        DateEqualFilter(Post.sent_at, 'Sent At'),
        DateEqualFilter(Post.created_at, 'Created At')
    ]

    column_formatters = {
        'profile': lambda v, c, m, p: m.profile.username if m.profile else '—'
    }

    form_columns = ('instagram_post_id', 'profile_id', 'media_type',
                    'is_sent', 'sent_at', 'sent_to', 'is_downloaded',
                    'file_path', 'errors_count')

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        flash('Нет прав доступа к этому разделу', 'error')
        return redirect(url_for('admin.index'))
