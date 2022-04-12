import sqlite3
from sqlalchemy import Table, create_engine
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy
import cx_Oracle
import pandas as pd
import dash

from models.models_delt import connect
from models.models_homepage import svarinngang_linje, svarinngang_kake, svarinngang_tbl1, klargjor_tbl1_svar
from models.models_grid import treeplot, table_grid, scatterplot_grid, histogram_grid, boxplot_grid, sammenlign_editert_ueditert
#from models.models_plots import bubble_plt_side
from models.models_enhet import enhetstabell1, enhet_plot, enhetstabell_store, update_columns, enhet_plot_bar_agg, offcanvas_innhold
#from models.models_tidsserie import display_time_series
from models.models_logg import logg_tabell
from models.models_kontroller import feilliste_tabell, innhent_feilliste, oppdater_feilliste_db, model_feilliste_figur, kontroll_enhetstabell_store, kontroll_update_columns, kontroll_enhetstabell, kontroll_offcanvas_innhold

from templates.homepage import Svarinngang
from templates.navbar import Navbar
#from templates.tidsserie import Tidsserie
from templates.grid import Grid
#from templates.vektet import Plots
from templates.enhet import Enhet
from templates.logg import Logg
from templates.kontroller import Kontroller

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table as dt
import dash_cytoscape as cyto
import dash_pivottable as dpt
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import dash_auth
import flask

from flask import request # for brukernavn

from datetime import datetime
from datetime import timedelta

import json

with open("config.json") as config: # Laster in valg fra config.json
    config = json.load(config)
conn, engine, db = connect()

#app
server = flask.Flask(__name__)
app = dash.Dash(__name__, server = server)
app.config.suppress_callback_exceptions = True

#Autentisering
VALID_USERNAME_PASSWORD_PAIRS = {
        'TEMP': 'TEMP'
    }

auth = dash_auth.BasicAuth(
    app,
VALID_USERNAME_PASSWORD_PAIRS
)

# Layout for plotly, bruker rgba. Red Green Blue Alpha, sistnevnte er hvor gjennomsiktig det er, ha mest mulig gjennomsiktig så kan bakgrunner enklere styres av CSS fil
edith_layout = go.layout.Template({ # Styler plotly figurer
    'data':{
        'scatter':[
            {'marker': 
                {'colorbar': 
                    {'outlinewidth': 0, 'ticks': ''}
                },
                'type': 'scatter'
            }
        ]
    },
    'layout': {
        'colorway': ["#1A9D49", "#C78800", "#1D9DE2", "#A3136C", "#909090", "#075745", "#0F2080", "#471F00", "#C775A7", "#000000"], #Default farger, brukes i rekkefølgen de står
        'font': {
            'color': '#000000'
        },
        'paper_bgcolor': 'rgba(0,0,0,0)', # Bakgrunn rundt grafen
        'plot_bgcolor': 'rgba(0,0,0,0)', # Bakgrunn i grafen
        'margin': {
            't':25
        }
    }
})
'''
#pio.templates.default = edith_layout # Velger egendefinert template
offcanvas = html.Div(
    dbc.Offcanvas(
            children = [
                html.Div(
                    id = "innhold_offcanvas"
                ),
                html.P("Kan lukkes ved å trykke på Esc")
            ],
            id="offcanvas",
            title="Informasjon om foretak",
            is_open = False,
            backdrop = False,
            scrollable = True,
            placement = "end"
        )
)
'''
#Layout
app.layout = html.Div([
    dcc.Store(id='clickdata', storage_type='local'), # Vet ikke hva clickdata er for
    dcc.Location(id = 'url', refresh = False),
    dbc.Row([
        dbc.Col(html.Img(src="assets/ssblogo.png", style = {"width": "300px"}), width=4), # Kan være praktisk med gjennomsiktig bakgrunn på logoen
        dbc.Col(html.H1("EDITH"))
    ], style = {"padding": "10px"}),
    html.Div(id = 'page-content'),
])

#Callbacks

@app.callback(Output('page-content', 'children'),
            [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/plots':
        return Plots()
    elif pathname == '/grid':
        return Grid()
    elif pathname == '/tidsserie':
        return Tidsserie()
    elif pathname == '/enhet':
        return Enhet()
    elif pathname == '/logg':
        return Logg()
    elif pathname == '/kontroller':
        return Kontroller()
    else:
        return Svarinngang()

from models.callbacks import get_callbacks

get_callbacks(app)



if __name__ == '__main__':
    app.run_server(debug = True, port=7878)

