from flask import redirect, request, flash
from flask.views import MethodView
from flask_login import current_user

from flaskbb.user.models import User
from flaskbb.forum.models import Post
from flaskbb.utils.helpers import render_template

from .karma import change_user_karma
from .post_rating import change_post_rating, get_all_post_rates_by_post
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
    def get(self):
        post_id = request.args.get("post_id", 0)
        post: Post = post_id and Post.query.filter_by(id=post_id).first_or_404()
        post_rate_records = get_all_post_rates_by_post(post)
        if post_rate_records:
            likes = {}
            dislikes= {}
            for post_rate_record in post_rate_records:
                if post_rate_record.change>0:
                    likes[post_rate_record.user]=post_rate_record.change
                else:
                    dislikes[post_rate_record.user]=post_rate_record.change
            
            return render_template(
                "features/karma/post_rating_dialog.html",
                likes=likes,
                dislikes=dislikes,
            )
        else:
            return render_template(
                "features/karma/post_rating_dialog.html",
                likes={"The post isn't rated yet":""},
                dislikes={"The post isn't rated yet":""},
            )

    def post(self):
        post_id = request.args.get("post_id", 0)
        post: Post = post_id and Post.query.filter_by(id=post_id).first_or_404()

        available, reason = is_user_can_rate_post(current_user, post)

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
