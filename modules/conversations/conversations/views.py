# -*- coding: utf-8 -*-
"""
    conversations.views
    ~~~~~~~~~~~~~~~~~~~

    This module contains the views for the
    conversations Plugin.

    :copyright: (c) 2018 by Peter Justin.
    :license: BSD License, see LICENSE for more details.
"""
import logging
import uuid
from functools import wraps

from flask import Blueprint, abort, flash, redirect, request, url_for
from flask.views import MethodView
from flask_babelplus import gettext as _
from flask_login import current_user, login_required

from flaskbb.extensions import db
from flaskbb.user.models import User
from flaskbb.utils.helpers import (
    format_quote,
    real,
    register_view,
    render_template,
    time_utcnow,
)
from flaskbb.utils.settings import flaskbb_config

from .forms import ConversationForm, MessageForm
from .models import Conversation, Message
from .utils import get_message_count, invalidate_cache


logger = logging.getLogger(__name__)

conversations_bp = Blueprint(
    "conversations_bp", __name__, template_folder="templates"
)


def check_message_box_space(redirect_to=None):
    """Checks the message quota has been exceeded. If thats the case
    it flashes a message and redirects back to some endpoint.

    :param redirect_to: The endpoint to redirect to. If set to ``None`` it
                        will redirect to the ``conversations_bp.inbox``
                        endpoint.
    """
    if get_message_count(current_user) >= flaskbb_config["MESSAGE_QUOTA"]:
        flash(
            _(
                "You cannot send any messages anymore because you have "
                "reached your message limit."
            ),
            "danger",
        )
        return redirect(redirect_to or url_for("conversations_bp.inbox"))


def require_message_box_space(f):
    """Decorator for :func:`check_message_box_space`."""
    # not sure how this can be done without explicitly providing a decorator
    # for this
    @wraps(f)
    def wrapper(*a, **k):
        return check_message_box_space() or f(*a, **k)

    return wrapper


class Inbox(MethodView):
    decorators = [login_required]

    def get(self):
        page = request.args.get("page", 1, type=int)
        # the inbox will display both, the recieved and the sent messages
        conversations = (
            Conversation.query.filter(
                Conversation.user_id == current_user.id,
                Conversation.draft == False,
                Conversation.trash == False,
            )
            .order_by(Conversation.date_modified.desc())
            .paginate(page, flaskbb_config["TOPICS_PER_PAGE"], False)
        )

        return render_template("inbox.html", conversations=conversations)


class ViewConversation(MethodView):
    decorators = [login_required]
    form = MessageForm

    def get(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        if conversation.unread:
            conversation.unread = False
            invalidate_cache(current_user)
            conversation.save()

        form = self.form()
        return render_template(
            "conversation.html", conversation=conversation, form=form
        )

    @require_message_box_space
    def post(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        form = self.form()
        if form.validate_on_submit():
            to_user_id = None
            # If the current_user is the user who recieved the message
            # then we have to change the id's a bit.
            if current_user.id == conversation.to_user_id:
                to_user_id = conversation.from_user_id
                to_user = conversation.from_user
            else:
                to_user_id = conversation.to_user_id
                to_user = conversation.to_user

            form.save(conversation=conversation, user_id=current_user.id)

            # save the message in the recievers conversation
            old_conv = conversation
            conversation = Conversation.query.filter(
                Conversation.user_id == to_user_id,
                Conversation.shared_id == conversation.shared_id,
            ).first()

            # user deleted the conversation, start a new conversation with just
            # the recieving message
            if conversation is None:
                conversation = Conversation(
                    subject=old_conv.subject,
                    from_user=real(current_user),
                    to_user=to_user,
                    user_id=to_user_id,
                    shared_id=old_conv.shared_id,
                )
                conversation.save()

            form.save(
                conversation=conversation, user_id=current_user.id, unread=True
            )
            invalidate_cache(conversation.to_user)

            return redirect(
                url_for(
                    "conversations_bp.view_conversation",
                    conversation_id=old_conv.id,
                )
            )

        return render_template(
            "conversation.html", conversation=conversation, form=form
        )


class NewConversation(MethodView):
    decorators = [login_required]
    form = ConversationForm

    def get(self):
        form = self.form()
        form.to_user.data = request.args.get("to_user")
        return render_template(
            "message_form.html", form=form, title=_("Compose Message")
        )

    def post(self):
        form = self.form()
        if "save_message" in request.form and form.validate():
            to_user = User.query.filter_by(display_name=form.to_user.data).first()

            shared_id = uuid.uuid4()

            form.save(
                from_user=current_user.id,
                to_user=to_user.id,
                user_id=current_user.id,
                unread=False,
                as_draft=True,
                shared_id=shared_id,
            )

            flash(_("Message saved."), "success")
            return redirect(url_for("conversations_bp.drafts"))

        if "send_message" in request.form and form.validate():
            check_message_box_space()

            to_user = User.query.filter_by(display_name=form.to_user.data).first()

            # this is the shared id between conversations because the messages
            # are saved on both ends
            shared_id = uuid.uuid4()

            # Save the message in the current users inbox
            form.save(
                from_user=current_user.id,
                to_user=to_user.id,
                user_id=current_user.id,
                unread=False,
                shared_id=shared_id,
            )

            # Save the message in the recievers inbox
            form.save(
                from_user=current_user.id,
                to_user=to_user.id,
                user_id=to_user.id,
                unread=True,
                shared_id=shared_id,
            )
            invalidate_cache(to_user)

            flash(_("Message sent."), "success")
            return redirect(url_for("conversations_bp.sent"))

        return render_template(
            "message_form.html", form=form, title=_("Compose Message")
        )


class EditConversation(MethodView):
    decorators = [login_required]
    form = ConversationForm

    def get(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        if not conversation.draft:
            flash(_("You cannot edit a sent message."), "danger")
            return redirect(url_for("conversations_bp.inbox"))

        form = self.form()
        form.to_user.data = conversation.to_user.username
        form.subject.data = conversation.subject
        form.message.data = conversation.first_message.message

        return render_template(
            "message_form.html", form=form, title=_("Edit Message")
        )

    def post(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        if not conversation.draft:
            flash(_("You cannot edit a sent message."), "danger")
            return redirect(url_for("conversations_bp.inbox"))

        form = self.form()

        if request.method == "POST":
            if "save_message" in request.form:
                to_user = User.query.filter_by(
                    username=form.to_user.data
                ).first()

                conversation.draft = True
                conversation.to_user_id = to_user.id
                conversation.first_message.message = form.message.data
                conversation.save()

                flash(_("Message saved."), "success")
                return redirect(url_for("conversations_bp.drafts"))

            if "send_message" in request.form and form.validate():
                check_message_box_space()

                to_user = User.query.filter_by(
                    username=form.to_user.data
                ).first()
                # Save the message in the recievers inbox
                form.save(
                    from_user=current_user.id,
                    to_user=to_user.id,
                    user_id=to_user.id,
                    unread=True,
                    shared_id=conversation.shared_id,
                )

                # Move the message from ``Drafts`` to ``Sent``.
                conversation.draft = False
                conversation.to_user = to_user
                conversation.date_created = time_utcnow()
                conversation.save()
                invalidate_cache(to_user)

                flash(_("Message sent."), "success")
                return redirect(url_for("conversations_bp.sent"))
        else:
            form.to_user.data = conversation.to_user.username
            form.subject.data = conversation.subject
            form.message.data = conversation.first_message.message

        return render_template(
            "message_form.html", form=form, title=_("Edit Message")
        )


class RawMessage(MethodView):
    decorators = [login_required]

    def get(self, message_id):

        message = Message.query.filter_by(id=message_id).first_or_404()

        # abort if the message was not the current_user's one or the one of the
        # recieved ones
        if not (
            message.conversation.from_user_id == current_user.id
            or message.conversation.to_user_id == current_user.id
        ):
            abort(404)

        return format_quote(
            username=message.user.username, content=message.message
        )


class MoveConversation(MethodView):
    decorators = [login_required]

    def post(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        conversation.trash = True
        conversation.save()

        return redirect(url_for("conversations_bp.inbox"))


class RestoreConversation(MethodView):
    decorators = [login_required]

    def post(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        conversation.trash = False
        conversation.save()
        return redirect(url_for("conversations_bp.trash"))


class DeleteConversation(MethodView):
    decorators = [login_required]

    def post(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        conversation.delete()
        return redirect(url_for("conversations_bp.trash"))


class SentMessages(MethodView):
    decorators = [login_required]

    def get(self):

        page = request.args.get("page", 1, type=int)

        conversations = (
            Conversation.query.filter(
                Conversation.user_id == current_user.id,
                Conversation.draft == False,
                Conversation.trash == False,
                db.not_(Conversation.to_user_id == current_user.id),
            )
            .order_by(Conversation.date_modified.desc())
            .paginate(page, flaskbb_config["TOPICS_PER_PAGE"], False)
        )

        return render_template("sent.html", conversations=conversations)


class DraftMessages(MethodView):
    decorators = [login_required]

    def get(self):

        page = request.args.get("page", 1, type=int)

        conversations = (
            Conversation.query.filter(
                Conversation.user_id == current_user.id,
                Conversation.draft == True,
                Conversation.trash == False,
            )
            .order_by(Conversation.date_modified.desc())
            .paginate(page, flaskbb_config["TOPICS_PER_PAGE"], False)
        )

        return render_template("drafts.html", conversations=conversations)


class TrashedMessages(MethodView):
    decorators = [login_required]

    def get(self):

        page = request.args.get("page", 1, type=int)

        conversations = (
            Conversation.query.filter(
                Conversation.user_id == current_user.id,
                Conversation.trash == True,
            )
            .order_by(Conversation.date_modified.desc())
            .paginate(page, flaskbb_config["TOPICS_PER_PAGE"], False)
        )

        return render_template("trash.html", conversations=conversations)


register_view(
    conversations_bp,
    routes=["/drafts"],
    view_func=DraftMessages.as_view("drafts"),
)
register_view(
    conversations_bp, routes=["/", "/inbox"], view_func=Inbox.as_view("inbox")
)
register_view(
    conversations_bp,
    routes=["/<int:conversation_id>/delete"],
    view_func=DeleteConversation.as_view("delete_conversation"),
)
register_view(
    conversations_bp,
    routes=["/<int:conversation_id>/edit"],
    view_func=EditConversation.as_view("edit_conversation"),
)
register_view(
    conversations_bp,
    routes=["/<int:conversation_id>/move"],
    view_func=MoveConversation.as_view("move_conversation"),
)
register_view(
    conversations_bp,
    routes=["/<int:conversation_id>/restore"],
    view_func=RestoreConversation.as_view("restore_conversation"),
)
register_view(
    conversations_bp,
    routes=["/<int:conversation_id>/view"],
    view_func=ViewConversation.as_view("view_conversation"),
)
register_view(
    conversations_bp,
    routes=["/message/<int:message_id>/raw"],
    view_func=RawMessage.as_view("raw_message"),
)
register_view(
    conversations_bp, routes=["/sent"], view_func=SentMessages.as_view("sent")
)
register_view(
    conversations_bp,
    routes=["/new"],
    view_func=NewConversation.as_view("new_conversation"),
)
register_view(
    conversations_bp,
    routes=["/trash"],
    view_func=TrashedMessages.as_view("trash"),
)
