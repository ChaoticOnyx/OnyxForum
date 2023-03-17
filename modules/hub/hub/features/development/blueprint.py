from flask import Blueprint
from flaskbb.utils.helpers import register_view
from .github_hook import GithubHook

development = Blueprint("development", __name__, template_folder="templates")

register_view(
    development,
    routes=['/github_hook'],
    view_func=GithubHook.as_view('github_hook')
)
