import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# define paths
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'data.sqlite')
template_dir = os.path.join(basedir, 'templates')

# app settings 
app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config["DEBUG"] = True

# Database configuration for Windows
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)