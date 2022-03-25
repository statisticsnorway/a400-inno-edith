import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

import sqlite3
from sqlalchemy import Table, create_engine
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy
import json

from templates.navbar import Navbar

from models.models_delt import connect

conn, engine, db = connect()

with open("config.json") as config: # Laster in valg fra config.json
    config = json.load(config)


nav = Navbar()
df_opt_var = pd.read_sql(f"SELECT distinct(VARIABEL) FROM {config['tabeller']['raadata']}", con=engine)
options_var = [{'label': x, 'value': x} for x in df_opt_var["VARIABEL"].unique()]

df_opt_foretak = pd.read_sql(f"SELECT distinct(orgnrNavn) FROM {config['tabeller']['raadata']}", con=engine) # Henter ut unike orgnrNavn
options_for = [{'label': x, 'value': x} for x in df_opt_foretak["orgnrNavn"]] # Lager {'label': 'value'} par for hvert unikt orgnrNavn


options_grupp = [{'label': x, 'value': x} for x in config["aggregater"]]

body = html.Div(dbc.Container([
    dcc.Store(id = 'table3_enhet'),
    dbc.Row([dbc.Col(html.Div(id = 'enhetsgraf_div'), width=12)]),
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id = 'grupp_enhet',
                multi = False,
                options = options_grupp,
                placeholder = "Velg gruppering",
                value = [config["default-valg"]["enhet"]["gruppering"]],
                #className = "dropdownmeny"
            )
        , width = 3),
        dbc.Col(
            dcc.Dropdown(
                id = 'var_enhet',
                multi = True, # Problem med editering dersom mer enn 1 variabel er valgt, alle variabler sine verdier overskrives, ikke bare den editerte.
                options = options_var,
                placeholder = "Velg variabler",
                value = [config["default-valg"]["enhet"]["gruppering"]],
                #className = "dropdownmeny"
            )
        , width = 3),
        dbc.Col(
            dcc.Dropdown(
                id = 'var_foretak',
                multi = False,
                options = options_for,
                placeholder = "Velg foretak",
                #className = "dropdownmeny" # Må kanskje lage ny class i CSS filen for denne. Den ser stilig ut men blir brukerfiendtlig som den er nå
            )
        , width = 3),
        dbc.Col(
            dbc.ButtonGroup(
                [
                    dbc.Button('Last inn', id='submit_table_enhet')
                ]
            )
        )
    ], style = {"padding":"10px"}),
    dbc.Row([dbc.Col(html.Div(id = 'enhetsgraf_div2'), width=6),
            dbc.Col(html.Div(id = 'enhetsgraf_div3'), width=6)]),
    dbc.Row([
        dbc.Col(
            dbc.ButtonGroup([
                dbc.Button('Editer', id='editer_enhet'),
                dbc.Button('Godta endringer', id='editer_enhet_godta'),
                dbc.Button("Åpne kommentarfelt foretak", id="offcanvas_knapp", n_clicks=0)
            ]), 
            width=4, style = {'float': 'right'})
    ],justify = 'end'),
    dbc.Row([dbc.Col(html.Div(id = 'enhetstabell1_div'), width=12)])
    ], className="container-grid", fluid=True)
)




def Enhet():
    layout = html.Div([
        nav,
        body
    ])
    return layout


