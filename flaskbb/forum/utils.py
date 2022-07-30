# -*- coding: utf-8 -*-
"""
    flaskbb.forum.utils
    ~~~~~~~~~~~~~~~~~~~

    Utilities specific to the FlaskBB forums module

    :copyright: (c) 2018 the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from flask import current_app
from flask_login import current_user

from .locals import current_forum
import hashlib


def force_login_if_needed():
    """
    Forces a login if the current user is unauthed and the current forum
    doesn't allow guest users.
    """

    if current_forum and should_force_login(current_user, current_forum):
        return current_app.login_manager.unauthorized()


def should_force_login(user, forum):
    return not user.is_authenticated and not (
        {g.id for g in forum.groups} & {g.id for g in user.groups}
    )

def hash_file(file):
    """"This function returns the SHA-1 hash
    of the file passed into it"""

    # make a hash object
    h = hashlib.sha1()

    # loop till the end of the file
    chunk = 0
    while chunk != b'':
        # read only 1024 bytes at a time
        chunk = file.read(1024)
        h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()
    
