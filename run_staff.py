from app import create_app
app = create_app(role_filter='staff') # Only loads staff routes
if __name__ == '__main__':
    app.run(debug=True, port=5002)