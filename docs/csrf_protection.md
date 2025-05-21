# CSRF Protection in Medical Spytool

## Overview
This document outlines the Cross-Site Request Forgery (CSRF) protection implemented in the Medical Spytool application.

## What is CSRF?
Cross-Site Request Forgery (CSRF) is an attack that forces authenticated users to submit a request to a web application against which they are currently authenticated. CSRF attacks exploit the trust that a web application has in a user's browser.

## Implementation in Medical Spytool

### Flask-WTF CSRF Protection
The Medical Spytool application uses Flask-WTF's CSRF protection, which leverages secure tokens to validate that requests originated from the application itself.

#### Key Components:

1. **CSRF Token Generation**
   - A unique token is generated for each user session
   - The token is tied to the user's session and has a limited lifetime
   - The token is cryptographically secure and cannot be predicted

2. **Form Implementation**
   - Every form in the application includes a hidden CSRF token field
   - Example implementation:
   ```html
   <form method="post" action="/submit">
       {{ form.csrf_token }}
       <!-- form fields -->
       <button type="submit">Submit</button>
   </form>
   ```

3. **Server Validation**
   - When a form is submitted, the server verifies the CSRF token
   - If the token is missing or invalid, the request is rejected
   - The verification happens automatically through Flask-WTF middleware

4. **AJAX Requests**
   - For AJAX requests, the CSRF token is included in headers
   - JavaScript fetches the token from a meta tag or form field
   - The token is sent with each AJAX request

### Protected Routes and Forms

The following routes and forms in Medical Spytool are protected against CSRF attacks:

1. **Authentication**
   - Login forms
   - Registration forms
   - Password change forms

2. **Data Modification**
   - Person creation/editing forms
   - Settings forms
   - Export configuration forms

3. **Critical Actions**
   - Delete actions
   - Export actions
   - Settings changes

### Testing CSRF Protection

We've created a dedicated testing tool (`tools/csrf_test.py`) to verify the CSRF protection on all forms:

1. The tool attempts to submit forms without CSRF tokens
2. It verifies that these requests are rejected
3. It provides a report showing which forms are properly protected

## Best Practices Followed

1. **Token Validation**
   - Tokens are validated on all state-changing requests (POST, PUT, DELETE)
   - Tokens include a timestamp and are regularly rotated
   - Tokens are securely stored in the user's session

2. **Secure Headers**
   - The application uses HTTP security headers to further protect against CSRF
   - Content Security Policy (CSP) is implemented to restrict sources of executable scripts
   - X-Frame-Options headers prevent clickjacking attacks that could be used in conjunction with CSRF

3. **Secure Defaults**
   - CSRF protection is enabled by default for all forms
   - Protection must be explicitly disabled for specific cases (which is rarely needed)

## Conclusion

The Medical Spytool application implements robust CSRF protection through Flask-WTF's CSRF middleware. All forms and state-changing actions require valid CSRF tokens, protecting users from cross-site request forgery attacks. Regular testing is conducted to ensure the protection is working correctly.

---

*Last Updated: May 15, 2025*
