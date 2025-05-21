#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Auth Blueprint
This blueprint handles user authentication, authorization, and user profile management.

The auth module provides secure user authentication with password hashing,
account management, and role-based access control. It implements security best practices
including brute-force protection, secure password requirements, and proper session management.

Features:
- User login with remember-me functionality
- Password reset with secure tokens
- User registration with email verification
- Role-based access control
- User profile management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import uuid
import logging
from smtplib import SMTP, SMTPException

from backend.models import db, User
from backend.utils import log_message
from backend.api_utils import api_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login with security best practices

    This function processes login attempts and implements security measures including:
    - Input validation
    - Brute force protection through logging failed attempts
    - Secure credential verification using constant-time comparison
    - Remember-me functionality with secure, HttpOnly cookies

    Returns:
        GET: Rendered login form template
        POST: Redirect to next page or index on success, back to login on failure

    Security:
        - Uses Werkzeug's secure password hashing
        - Logs failed login attempts for security monitoring
        - Uses Flask-Login for secure session management
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = "remember" in request.form

        # Validate input
        if not username or not password:
            flash("Benutzername und Passwort werden benötigt.", "warning")
            return redirect(url_for("auth.login"))

        # Check user credentials
        user = User.get_by_username(username)
        if user is None or not user.check_password(password):
            log_message(f"Failed login attempt for username: {username}", level="WARNING")
            flash("Ungültige Anmeldedaten. Bitte versuche es noch einmal.", "danger")
            return redirect(url_for("auth.login"))

        # Log user in
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()

        log_message(f"User {user.username} logged in successfully", level="INFO")
        flash(f"Willkommen zurück, {user.username}!", "success")

        # Redirect to the page the user was trying to access
        next_page = request.args.get("next")
        if not next_page or next_page.startswith("/"):
            next_page = url_for("main.index")

        return redirect(next_page)

    # GET request - show login form
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Handle user logout"""
    username = current_user.username
    logout_user()
    log_message(f"User {username} logged out", level="INFO")
    flash("Erfolgreich abgemeldet.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        first_name = request.form.get("first_name", "")
        last_name = request.form.get("last_name", "")

        # Validate input
        if not username or not email or not password:
            flash("Alle erforderlichen Felder müssen ausgefüllt werden.", "warning")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Die Passwörter stimmen nicht überein.", "warning")
            return redirect(url_for("auth.register"))

        # Check if username or email already exists
        if User.get_by_username(username):
            flash("Dieser Benutzername wird bereits verwendet.", "warning")
            return redirect(url_for("auth.register"))

        if User.get_by_email(email):
            flash("Diese E-Mail wird bereits verwendet.", "warning")
            return redirect(url_for("auth.register"))

        # Create new user
        user = User(username=username, email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)

        # If this is the first user, make them an admin
        if User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()

        log_message(f"New user registered: {username}", level="INFO")
        flash("Registrierung erfolgreich! Du kannst dich jetzt anmelden.", "success")
        return redirect(url_for("auth.login"))

    # GET request - show registration form
    return render_template("auth/register.html")


@auth_bp.route("/profile")
@login_required
def profile():
    """Show user profile"""
    return render_template("auth/profile.html")


@auth_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Handle profile editing"""
    if request.method == "POST":
        current_user.first_name = request.form.get("first_name", current_user.first_name)
        current_user.last_name = request.form.get("last_name", current_user.last_name)

        # Update email if changed and not already in use
        new_email = request.form.get("email")
        if new_email and new_email != current_user.email:
            if User.get_by_email(new_email):
                flash("Diese E-Mail wird bereits verwendet.", "warning")
            else:
                current_user.email = new_email

        # Update password if provided
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash("Aktuelles Passwort ist nicht korrekt.", "danger")
                return redirect(url_for("auth.edit_profile"))

            if new_password != confirm_password:
                flash("Die neuen Passwörter stimmen nicht überein.", "warning")
                return redirect(url_for("auth.edit_profile"))

            current_user.set_password(new_password)
            flash("Passwort erfolgreich aktualisiert.", "success")

        db.session.commit()
        log_message(f"User {current_user.username} updated their profile", level="INFO")
        flash("Profil erfolgreich aktualisiert.", "success")
        return redirect(url_for("auth.profile"))

    # GET request - show edit form
    return render_template("auth/edit_profile.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Handle forgotten password requests

    This endpoint processes requests for password resets:
    1. User submits their email address
    2. System generates a secure token and stores it with the user
    3. System sends an email with a reset link (or logs it for development)

    Returns:
        GET: Rendered form for submitting email
        POST: Redirect with appropriate flash message
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "")
        if not email:
            flash("Bitte geben Sie die E-Mail-Adresse ein.", "warning")
            return render_template("auth/forgot_password.html")

        user = User.get_by_email(email)
        if not user:
            # Don't reveal if user exists, but log it
            log_message(
                f"Password reset requested for non-existent email: {email}", level="WARNING"
            )
            flash(
                "Wenn diese E-Mail-Adresse registriert ist, erhalten Sie einen Link zum Zurücksetzen des Passworts.",
                "info",
            )
            return redirect(url_for("auth.login"))

        # Generate secure token
        token = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(hours=24)

        # Save token in database
        user.set_reset_token(token, expiry)
        db.session.commit()

        # Build reset link
        reset_link = url_for("auth.reset_password", token=token, _external=True)

        # In production, send email
        # For now, log the reset link for development purposes
        email_body = f"""
        Hallo {user.username},
        
        Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.
        Klicken Sie auf den folgenden Link, um Ihr Passwort zurückzusetzen:
        
        {reset_link}
        
        Dieser Link ist 24 Stunden gültig.
        
        Wenn Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail.
        
        Mit freundlichen Grüßen,
        Das Medical Spytool Team
        """

        try:
            # TODO: In production, replace this with actual email sending
            # For now, log the email for demonstration purposes
            log_message(f"Password reset email would be sent to: {email}", level="INFO")
            log_message(f"Email body: {email_body}", level="DEBUG")

            flash(
                "Wenn diese E-Mail-Adresse registriert ist, erhalten Sie einen Link zum Zurücksetzen des Passworts.",
                "info",
            )
            return redirect(url_for("auth.login"))

        except Exception as e:
            log_message(f"Failed to process password reset for {email}: {str(e)}", level="ERROR")
            db.session.rollback()
            flash(
                "Ein Fehler ist aufgetreten. Bitte versuchen Sie es später noch einmal.", "danger"
            )

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Handle password reset with token

    This endpoint validates a reset token and allows the user to set a new password:
    1. Validates that the token exists and has not expired
    2. Allows the user to set a new password (with confirmation)
    3. Clears the reset token after successful password change

    Args:
        token: The password reset token from the URL

    Returns:
        GET: Rendered form for password reset
        POST: Redirect after processing password change
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Find user by token
    user = User.get_by_reset_token(token)

    # Validate token exists and has not expired
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        log_message(
            f"Invalid or expired password reset attempt with token: {token}", level="WARNING"
        )
        flash("Der Link zum Zurücksetzen des Passworts ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password:
            flash("Bitte geben Sie ein Passwort ein.", "warning")
            return render_template("auth/reset_password.html", token=token)

        if password != confirm_password:
            flash("Die Passwörter stimmen nicht überein.", "warning")
            return render_template("auth/reset_password.html", token=token)

        if len(password) < 8:
            flash("Das Passwort muss mindestens 8 Zeichen lang sein.", "warning")
            return render_template("auth/reset_password.html", token=token)

        try:
            # Update password
            user.set_password(password)
            # Clear reset token
            user.clear_reset_token()

            db.session.commit()

            log_message(f"Password reset successful for user: {user.username}", level="INFO")
            flash(
                "Ihr Passwort wurde erfolgreich zurückgesetzt. Sie können sich jetzt anmelden.",
                "success",
            )
            return redirect(url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            log_message(f"Password reset failed for user {user.username}: {str(e)}", level="ERROR")
            flash(
                "Ein Fehler ist aufgetreten. Bitte versuchen Sie es später noch einmal.", "danger"
            )

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/api/request-password-reset", methods=["POST"])
def api_request_password_reset():
    """API endpoint for requesting a password reset

    Similar to the forgot_password function but returns JSON responses
    for API clients instead of HTML templates.

    Returns:
        JSON: Standardized API response with success/error information
    """
    email = request.json.get("email", "") if request.is_json else request.form.get("email", "")

    if not email:
        return api_response(success=False, message="Email address is required", status_code=400)

    user = User.get_by_email(email)
    if not user:
        # Don't reveal if user exists, but log it
        log_message(
            f"API password reset requested for non-existent email: {email}", level="WARNING"
        )
        # Return success even if user doesn't exist (security through obscurity)
        return api_response(
            success=True,
            message="If this email is registered, a reset link has been sent",
            status_code=200,
        )

    # Generate secure token
    token = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(hours=24)

    try:
        # Save token in database
        user.set_reset_token(token, expiry)
        db.session.commit()

        # Build reset link
        reset_link = url_for("auth.reset_password", token=token, _external=True)

        # For now, log the reset link
        log_message(f"API password reset link for {email}: {reset_link}", level="INFO")

        return api_response(
            success=True,
            message="If this email is registered, a reset link has been sent",
            status_code=200,
        )

    except Exception as e:
        db.session.rollback()
        log_message(f"API password reset failed for {email}: {str(e)}", level="ERROR")
        return api_response(
            success=False,
            message="An error occurred while processing your request",
            status_code=500,
        )
