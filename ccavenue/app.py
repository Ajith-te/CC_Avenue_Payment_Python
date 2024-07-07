from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS

from ccavenue.database import db
from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI
from ccavenue.refund import refund_bp
from ccavenue.payment_invoice import invo_bp

app = Flask(__name__)
CORS(app)

# Register the Blueprint
app.register_blueprint(refund_bp)
app.register_blueprint(invo_bp)


app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return 'FIA payment server by CCavenue v.002'
