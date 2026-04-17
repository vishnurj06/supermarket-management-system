from app import create_app

app = create_app()
app.secret_key = 'customer_super_secret_key_123'
app.config['SESSION_COOKIE_NAME'] = 'customer_session_cookie'

if __name__ == '__main__':
    app.run(debug=True, port=5000)