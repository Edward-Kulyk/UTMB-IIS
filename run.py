from app import create_app, db

# from waitress import serve

app = create_app()

if __name__ == "__main__":
    app.run()
