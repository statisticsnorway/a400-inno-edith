import sqlite3
from sqlalchemy import Table, create_engine
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy

import dash_table as dt
import dash_bootstrap_components as dbc
import dash_core_components as dcc

import json

with open("config.json") as config: # Laster in valg fra config.json
    config = json.load(config)

#Funksjon som kobler opp mot .sqlite
def connect():
    conn = sqlite3.connect(f"{config['data']['filsti']}/edith.sqlite", timeout=15) #Må endres hvis koblingen skal være opp mot dynarev
    engine = create_engine(f"sqlite:///{config['data']['filsti']}/edith.sqlite")
    db = SQLAlchemy()
    return conn, engine, db


def cardify_figure(id, figure, tittel=None): # Putter en figur inn i et dash bootstrap components card
    if tittel:
        return dbc.Card(dbc.CardBody([html.H4(tittel), dcc.Graph(id = id,figure=figure)]))
    else:
        return dbc.Card(dbc.CardBody(dcc.Graph(id = id,figure=figure)))



#Funksjoner
def table(id, data, columns, filterable=True, column_selectable=False):
    if filterable == True:
        tabell = dt.DataTable(
            id = id,
            style_cell={'textAlign': 'left'},
            sort_action='native',
            data = data,
            columns = columns,
            column_selectable = column_selectable,
            filter_action='native',
            editable = False,
            page_action = 'native',
            page_size = 100,
            sort_mode = 'multi',
        )
    else:
        tabell = dt.DataTable(
            id = id,
            style_cell={'textAlign': 'left'},
            sort_action='native',
            data = data,
            columns = columns,
            page_action = 'native',
            page_size = 20,
            sort_mode = 'multi',
        )
    return tabell

def main():
    import pandas as pd
    conn, engine, db = connect()
    print(pd.read_sql(f"select * from {config['tabeller']['raadata']}", con = engine).head())
    print("Sett inn tester her")

if __name__ == "__main__":
    main()
print("models_delt.py lastet")