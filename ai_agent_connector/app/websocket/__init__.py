"""
WebSocket module for real-time OntoGuard validation.

This module provides WebSocket endpoints for real-time semantic validation
of AI agent actions using the OntoGuard framework.
"""

from .ontoguard_ws import register_websocket_handlers, get_socketio

__all__ = ['register_websocket_handlers', 'get_socketio']
