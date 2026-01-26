"""
Prompt Engineering Studio
Visual editor for customizing SQL generation prompts
"""

from flask import Blueprint

prompt_bp = Blueprint('prompts', __name__, url_prefix='/prompts')

from . import routes

