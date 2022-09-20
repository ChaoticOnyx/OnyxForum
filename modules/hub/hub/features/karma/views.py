from flask import redirect, request, flash
from flask.views import MethodView
from flask_login import current_user

from flaskbb.user.models import User
from flaskbb.forum.models import Post
from flaskbb.utils.helpers import render_template

from .karma import change_user_karma
from .post_rating import change_post_rating, get_all_users_and_change_rated_post
from .render import is_user_can_change_karma, is_user_can_rate_post


class KarmaView(MethodView):
    def post(self):
        user_id = request.args.get("user_id", 0)
        user = user_id and User.query.filter_by(id=user_id).first_or_404()

        post_id = request.args.get("post_id", 0)
        post: Post = post_id and Post.query.filter_by(id=post_id).first_or_404()

        available, reason = is_user_can_change_karma(current_user, user)

        if available:
            if "Like" in request.form:
                change_user_karma(user.discord, current_user.discord, 1)
            elif "Dislike" in request.form:
                change_user_karma(user.discord, current_user.discord, -1)
            elif "Reset" in request.form:
                change_user_karma(user.discord, current_user.discord, 0)
        else:
            flash("Karma change error: " + reason, "danger")

        if post:
            return redirect(post.url)
        return redirect(user.url)


class PostRateView(MethodView):
    def post(self):
        post_id = request.args.get("post_id", 0)
        post: Post = post_id and Post.query.filter_by(id=post_id).first_or_404()

        available, reason = is_user_can_rate_post(current_user, post)
        if "Users" in request.form:
            users = get_all_users_and_change_rated_post(post)
            if users:
                likes = {}
                dislikes= {}
                for user in users.keys():
                    if users[user]>0:
                        likes[user]=users[user]
                    else:
                        dislikes[user]=users[user]
                
                return render_template(
                    "features/karma/post_rating_dialog.html",
                    likes=likes,
                    dislikes=dislikes,
                )
            else:
                return 'No one don\'t rate this post yet!'

        if available:
            if "Like" in request.form:
                change_post_rating(current_user, post, 1)
            elif "Dislike" in request.form:
                change_post_rating(current_user, post, -1)
            elif "Reset" in request.form:
                change_post_rating(current_user, post, 0)
        else:
            flash("Post rate error: " + reason, "danger")

        return redirect(post.url)
