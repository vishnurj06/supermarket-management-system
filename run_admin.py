from app import create_app

app = create_app(role_filter='admin')
app.secret_key = 'admin_super_secret_key_123'
app.config['SESSION_COOKIE_NAME'] = 'admin_session_cookie'

if __name__ == '__main__':
    app.run(debug=True, port=5001)