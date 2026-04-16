from app import create_app
app = create_app(role_filter='admin') # Only loads admin routes
if __name__ == '__main__':
    app.run(debug=True, port=5001)