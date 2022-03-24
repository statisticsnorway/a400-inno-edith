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

import time
import datetime as date

from datetime import datetime
from datetime import timedelta

from templates.navbar import Navbar

from models.models_delt import connect

conn, engine, db = connect()

with open("config.json") as config:
    config = json.load(config)

nav = Navbar()

df_opt_var = pd.read_sql(f"SELECT distinct(Variabel) FROM {config['tabeller']['raadata']}", con=engine)
options_var = [{'label': x, 'value': x} for x in df_opt_var["Variabel"].unique()]

options_grupp = [{'label': x, 'value': x} for x in config["aggregater"]]



body = html.Div([dbc.Container([
    dcc.Store('data_grid'),
    dbc.Row([
        dbc.Col(
            html.Div(id = 'test'), width=12
        )
    ]),
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id = 'grupp',
                multi = True,
                options = options_grupp,
                value = [config["default-valg"]["grid"]["gruppering"]],
                placeholder = "Velg gruppering"
            )
        , width = 3),
        dbc.Col(
            dcc.Dropdown(
                id = 'var',
                multi = True,
                options = options_var,
                value = [config["default-valg"]["grid"]["variabel"]],
                placeholder = "Velg variabler"
            )
        , width = 3),
        dbc.Col(
            dbc.ButtonGroup(
                [
                    dbc.Button('Last inn / Tilbake', id='submit_table'),
                ]
            )
        )
    ], style = {"padding":"10px"}),
    dbc.Row([dbc.Col(html.Div(id = 'test'), width=10)]),
    dbc.Row([
        dbc.Col(
            html.Div(
                dbc.Tabs([
                    dbc.Tab([
                        dbc.Row(html.Div(id = "scatterplot_div_grid")),
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(
                                    id = 'x_scatter_grid',
                                    options = options_var,
                                    placeholder = "Velg x variabel",
                                    className="egendropdown"
                                )
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id = 'y_scatter_grid',
                                    options = options_var,
                                    placeholder = "Velg y variabel",
                                    className="egendropdown"
                                )
                            ),
                            dbc.Col(
                                dcc.Checklist(
                                    id = "checklist_scatter_grid",
                                    options = [
                                        {"label": "Fjern 0-verdier", "value": "fjern"}
                                    ]
                                )
                            )
                        ])
                    ], label="Scatterplot"),
                    dbc.Tab([
                        dbc.Row(html.Div(id = "histogram_div_grid")),
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(
                                    id = "variabel_histogram_grid",
                                    options = options_var,
                                    placeholder = "Velg variabel",
                                    className = "egendropdown"
                                )
                            ),
                            dbc.Col(
                                dcc.Input(
                                    id="bins_histogram_grid",
                                    type="number",
                                    placeholder="Sett inn grenseverdi",
                                    value = 10
                                )
                            ),
                            dbc.Col(
                                dcc.Checklist(
                                    id = "checklist_histogram_grid",
                                    options = [
                                        {"label": "Fjern 0-verdier", "value": "fjern"}
                                    ]
                                )
                            )
                        ])
                        ], label="Histogram"
                    ),
                    dbc.Tab([
                        dbc.Row([html.Div(id = "boxplot_div_grid")]),
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(
                                    id = "variabel_boxplot_grid",
                                    options = options_var,
                                    placeholder = "Velg variabel",
                                    className = "egendropdown"
                                )
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id = "boxpoints_boxplot_grid",
                                    options = [
                                        {"label": "Alle", "value": "all"},
                                        {"label": "utliggere", "value": "outliers"},
                                        {"label": "Suspected outliers", "value": "suspectedoutliers"}
                                    ],
                                    value = "all",
                                    className = "egendropdown"
                                )
                            ),
                            dbc.Col(
                                dcc.Checklist(
                                    id = "checklist_boxplot_grid",
                                    options = [
                                        {"label": "Fjern 0-verdier", "value": "fjern"}
                                    ]
                                )
                            )
                        ])
                    ], label = "Boxplot")
                ]), id = "grid-left_fig"
            ), width=6
        ),
        dbc.Col(
            html.Div(id = 'treemap_div'), width=6
        )
    ]),
    dbc.Row([
        dbc.Col(
            html.Div(id = 'tabell_div_grid'), width=12
        )
    ]),
], className="container-grid", fluid=True)])

################################################
# Eksperiment med sammenligne editert/ueditert #
try:
    datoer = pd.read_sql(f"SELECT distinct(Log_tid) FROM {config['tabeller']['editeringer']}", con=engine)
except:
    datoer = pd.DataFrame(data = {"Log_tid": [date.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]})

datoer["Log_tid"] = pd.to_datetime(datoer["Log_tid"])

daterange = pd.date_range(
    datoer.min()[0],
    datoer.max()[0],
    freq = "d"
)

dager = {}
for i in range(len(daterange)):
    dager[int(time.mktime(daterange[i].timetuple()))] = daterange[i].date()

sammenligne = dbc.Container(
    [
        html.Div([
            dbc.Accordion([
                dbc.AccordionItem([
                    dbc.Row([html.H1("Eksempel på sammenligning av editerte og uediterte")]),
                    dbc.Row([html.Div(id = "TEST")]),
                    dbc.Row([
                        dbc.Col([
                            dcc.Slider(
                                id = "slider",
                                min = int(time.mktime(datoer.min()[0].timetuple())),
                                max = int(time.mktime(datoer.max()[0].timetuple())),
                                value = int(time.mktime(datoer.max()[0].timetuple())),
                                marks = dager,
#                                    int(time.mktime(datoer.min()[0].timetuple())): str(datoer.min()[0]),
#                                    int(time.mktime(datoer.max()[0].timetuple())): str(datoer.max()[0])
#                                },
                                tooltip = {
                                    "always_visible": True
                                }
                            )
                        ])
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div(id = "sammenligning")
                        ])
                    ])
                ], title = "Sammenlign editerte og uediterte data")
            ], start_collapsed = True)
        ])
    ], className = "container-grid", fluid = True
)
################################################


def Grid():
    layout = html.Div([
        nav,
        sammenligne,
        body,
    ])
    return layout


