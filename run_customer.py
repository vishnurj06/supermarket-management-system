from app import create_app
app = create_app(role_filter='customer') # Only loads customer routes
if __name__ == '__main__':
    app.run(debug=True, port=5000)