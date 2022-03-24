import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

import dash_table as dt

import sqlite3
from sqlalchemy import Table, create_engine
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy

from templates.navbar import Navbar

from models.models_delt import connect

conn, engine, db = connect()

nav = Navbar()

body = dbc.Container([
    dcc.Store(id = 'logg_data'),
    dbc.Row([
        dbc.Col(
            html.Div(id = 'tabell_logg')
        )
    ])
], className="container-grid", fluid=True)

def Logg():
    layout = html.Div([
        nav,
        body
    ])
    return layout