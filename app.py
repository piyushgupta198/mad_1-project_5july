from flask import Flask
from controllers.create_database_instance import create_tables
from controllers.database import db
from controllers.config import Config

def create_app():   
    app = Flask(__name__) 
    app.config.from_object(Config)
    db.init_app(app)
    app.app_context().push()

    return app

app = create_app()

from controllers.general_routes import *

if __name__ == '__main__':
    create_tables()
    app.run(debug=True) 