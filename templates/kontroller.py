import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import dash_table as dt
import plotly.express as px

import pandas as pd
import numpy as np
import json
import sqlite3
from sqlalchemy import Table, create_engine

from models.models_delt import connect

conn, engine, db = connect()


from templates.navbar import Navbar
#from models.models import connect
import json
with open("config.json") as config:
    config = json.load(config)


try:
    #Kan ha med "alle" hvis ikke det er en for store fil til at appen henger
    #feilliste_valg = np.insert(pd.read_csv(config['data']['filsti'] + "/feilliste.csv")['feilliste'].unique(), 0, 'Alle')
    feilliste_valg = pd.read_csv(config['data']['filsti'] + "/feilliste.csv")['feilliste'].unique()
except:
    feilliste_valg = ["Ingen feillister tilgjengelig"]

feilliste_valg = [item.replace(',', '') for item in feilliste_valg]
options_grupp = [{'label': x, 'value': x} for x in feilliste_valg]


# Input enhet
df_opt_foretak = pd.read_sql(f"SELECT distinct(orgnrNavn) FROM {config['tabeller']['raadata']}", con=engine) # Henter ut unike orgnrNavn
options_enhet = [{'label': x, 'value': x} for x in df_opt_foretak["orgnrNavn"]] # Lager {'label': 'value'} par for hvert unikt orgnrNavn


nav = Navbar()


body = dbc.Container([

    dcc.Store(id = 'feilliste_tabell'),

    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id = 'velg_feilliste',
                multi = True,
                options = options_grupp,
                placeholder = "Velg feilliste",
                value = [feilliste_valg[0]],
                #className = "dropdownmeny"
            )
        , width = 5),
        dbc.Col(
            dbc.ButtonGroup( 
                [dbc.Button('Lagre kommentar', id = 'godta_endring')]
            )         
        ),
        dbc.Col(
            html.Div(id = 'tabell_feilliste')
        )
    ]),


    dbc.Row([dbc.Col(html.Div(id = 'figur_feilliste_vars'), width=12)]),

    dcc.Store(id = 'kontroll_tabell_enhet'),

    dbc.Row([dbc.Col(dbc.ButtonGroup([

            dbc.Button('Godta endringer', id='kontroll_editer_enhet_godta'),
            dbc.Button("Enhetsopplysninger", id="kontroll_offcanvas_knapp", n_clicks=0)]), 

        width=3, style = {'float': 'right'})
    ],justify = 'end'),

    dbc.Row(dbc.Col(html.Div(id = 'kontroll_enhet_tabell_div'))),

    
], className="container-grid", fluid=True)


sidebar = html.Div(
    dbc.Offcanvas(
            children = [
                html.Div(
                    id = "innhold_offcanvas"
                ),
                html.P("Kan lukkes ved å trykke på Esc")
            ],
            id="kontroll_offcanvas",
            title="Informasjon om foretak",
            is_open = False,
            backdrop = False,
            scrollable = True,
            placement = "end"
        )
)

def Kontroller():
    layout = html.Div([
        nav,
        body,
        sidebar
    ])
    return layout