"""
Embeddable query widgets for blogs and websites
"""

from flask import Blueprint

widget_bp = Blueprint('widget', __name__, url_prefix='/widget')

from . import routes

