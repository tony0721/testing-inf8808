from flask_failsafe import failsafe

@failsafe
def create_app():
    from app import app  # pylint: disable=import-outside-toplevel
    return app.server

if __name__ == "__main__":
    create_app().run(port="8050", debug=True)