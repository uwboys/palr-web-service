# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response, abort, make_response
from bson.json_util import dumps
from time import gmtime, strftime, time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
from models.user import User
from global_constants import global_countries, global_ethnicities
from datetime import datetime, timedelta
from bson import ObjectId
import atexit
import jwt
import logging
import pymongo
import re
import validators
import global_constants
from pymongo import MongoClient
from flask_socketio import SocketIO, emit
from flask import Flask
from flask import session
from flask_socketio import emit, join_room, leave_room
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from random import randint

socketio = SocketIO(app)

mongo = PyMongo(app, config_prefix='MONGO')

clients = {}
