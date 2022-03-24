import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

import sqlite3
from sqlalchemy import Table, create_engine
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy

from templates.navbar import Navbar

from models.models_delt import connect

import json

conn, engine, db = connect()


with open("config.json") as config: # Laster in valg fra config.json
    config = json.load(config)


nav = Navbar()

#Data
#henter ut felt_id variabler
df_opt_var = pd.read_sql(f"SELECT distinct(FELT_ID) FROM {config['tabeller']['svarinngang']}", con=engine) # Skal kanskje rename FELT_ID til noe annet etterhvert?
options_var = [{'label': x, 'value': x} for x in df_opt_var["FELT_ID"].unique()]

df_svar = pd.read_sql(f'SELECT * from {config["tabeller"]["svarinngang"]}', con=engine, parse_dates=['INN_DATO'])

homepage_dropdown = dcc.Dropdown(
                id = 'dropdown_svarinngang',
                multi = False,
                options = options_var,
                placeholder = "Velg variabel",
                value = 'intfou',
                className = "dropdownmeny")

homepage_input = dcc.Input(id="input_svarinngang",
                          type="number",
                          placeholder="Sett inn grenseverdi",
                          value = 20000)
"""
body = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(id = 'linje'),
                    ], width = 6
                ),
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            dbc.Row([
                                dbc.Col(homepage_dropdown, width = 5),
                                dbc.Col(homepage_input, width = 5)
                            ], style={"padding-top":"10px"})
                        ])
                    ]),
                    dbc.Row([
                        dbc.Col(
                            html.Div(id = "pie")
                        )
                    ])
                ], width = 6)
            ]
        ),
        dbc.Row([
            dbc.Col([
                html.Div(id = "forside-tabell")
            ])
        ])
    ],
    className="mt-4",
)
#Test den under for å se dropdown/input over hverandre istedenfor side by side
"""
body = dbc.Container(
    [
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(homepage_dropdown, width = 5)
                ]),
                dbc.Row([
                    dbc.Col(homepage_input, width = 5)
                ])
            ], width=3),
            dbc.Col([
                html.Div(id = "forside_tabell")
            ], width=9)
        ]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(id = 'linje'),
                    ], width = 6
                ),
                dbc.Col([
                    dbc.Row([
                        dbc.Col(
                            html.Div(id = "pie")
                        )
                    ])
                ], width = 6)
            ]
        )
    ],
    className="container-grid", fluid=True,
)





def Svarinngang():
    layout = html.Div([
        nav,
        body,
    ])
    return layout


