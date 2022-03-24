import sqlite3
from sqlalchemy import Table, create_engine
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy

import dash_table as dt
import dash_bootstrap_components as dbc
import dash_core_components as dcc

import json

with open("config.json") as config: # Laster in valg fra config.json
    code = json.load(config)

#Funksjon som kobler opp mot .sqlite
def connect():
    conn = sqlite3.connect(f"{code['data']['filsti']}/edith.sqlite", timeout=15) #Må endres hvis koblingen skal være opp mot dynarev
    engine = create_engine(f"sqlite:///{code['data']['filsti']}/edith.sqlite")
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
            #style_as_list_view = True,
            #style_cell_conditional=[
            #    {
            #        'if': {'column_id': c},
            #        'textAlign': 'left'
            #    } for c in ['Date', 'Region']
            #    ],
            #    style_data_conditional=[
            #        {
            #            'if': {'row_index': 'odd'},
            #            'backgroundColor': 'rgb(248, 248, 248)'
            #        }
            #    ],
            #    style_header={
            #        'backgroundColor': 'rgb(230, 230, 230)',
            #        'fontWeight': 'bold'
            #}
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
            #style_as_list_view = True,
            #style_cell_conditional=[
            #    {
            #        'if': {'column_id': c},
            #        'textAlign': 'left'
            #    } for c in ['Date', 'Region']
            #    ],
            #    style_data_conditional=[
            #        {
            #            'if': {'row_index': 'odd'},
            #            'backgroundColor': 'rgb(248, 248, 248)'
            #        }
            #    ],
            #    style_header={
            #        'backgroundColor': 'rgb(230, 230, 230)',
            #        'fontWeight': 'bold'
            #}
        )
    return tabell

def main():
    print("Sett inn tester her")

if __name__ == "__main__":
    main()
print("models_delt.py lastet")