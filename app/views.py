"""
Main views blueprint for HireSense.

Provides the root dashboard route that redirects authenticated users
to their role-specific dashboard (admin, manager, or employee).
"""
from flask import Blueprint, redirect, url_for
from flask_login import current_user, login_required

views_bp = Blueprint("views", __name__)


def _role_dashboard_url():
    """
    Get the dashboard URL for the current user's role.
    
    :returns: URL string for the appropriate dashboard.
    :rtype: str
    """
    role = current_user.role
    if role == "admin":
        return url_for("admin.dashboard")
    elif role == "manager":
        return url_for("manager.dashboard")
    return url_for("employee.dashboard")


@views_bp.route("/")
@login_required
def dashboard():
    """
    Root dashboard route.

    Redirects authenticated users to their role-specific dashboard.

    :returns: Redirect to the appropriate dashboard based on user role.
    :rtype: flask.Response
    """
    return redirect(_role_dashboard_url())
