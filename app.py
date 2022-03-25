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
#from templates.uvektet import Grid

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
        'TEST': 'TEST'
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


##############################################
# Eksperimentell, sammenligne editert/ueditert.
# Ligger på svarinngang siden foreløpig, kan lett flyttes
@app.callback(Output("TEST", "children"),
              Input("slider", "value"))
def TEST(click):
    print(click)
    return html.H1(str(click))


##############################################
###############
# Svarinngang #
###############

@app.callback(Output('linje', 'children'),
               [Input('dropdown_svarinngang', 'value'),
                Input('input_svarinngang', 'value')])
def linje_svar(dropdown, input_svarinngang):
    return svarinngang_linje(dropdown, input_svarinngang)



@app.callback(Output('pie', 'children'),
               [Input('dropdown_svarinngang', 'value'),
                Input('input_svarinngang', 'value')])
def kake_svar(dropdown, hm_input):
    return svarinngang_kake(dropdown, hm_input)



@app.callback(Output('forside_tabell', 'children'),
               [Input('dropdown_svarinngang', 'value'),
                Input('input_svarinngang', 'value')])
def tbl1_svar(dropdown, hm_input):
    return svarinngang_tbl1(dropdown, hm_input)


########
# Grid #
########

@app.callback(Output("test", "children"),
              Input("treemap", "clickData"))
def test(click):
    print(click)
    return html.H1(str(click))

@app.callback(
    Output('drilldown_grid', 'children'),
    [
        Input('grupp', 'value'),
        Input('data_grid', 'data')
    ]
)
def drilldown_grid(aggregater, data):
    test = [html.H5("Tester")]
    print(test)
    df = pd.DataFrame(data)
    for i in aggregater:
        test = test + [dcc.Dropdown(
                id = i,
                multi = True,
                options = [{'label': x, 'value': x} for x in list(df[i].unique())],
                placeholder = "Velg gruppering"
            )]
    print("Her skal dropdown være " + str(test))
    return html.Div([
        test
    ])


@app.callback([Output('treemap_div', 'children'),
              Output('data_grid', 'data')],
              [Input('submit_table', 'n_clicks'),
               State('var', 'value'),
               State('grupp', 'value')])
def treemap_plot(n_click, var, grupp):
    return treeplot(n_click, var, grupp)

@app.callback(
    Output('tabell_div_grid', 'children'),
    [
        Input('data_grid', 'data'),
        State('grupp', 'value'),
        Input('treemap', 'clickData')
    ]
)
def make_table_grid(data, grupp, clickData):
    return table_grid(data, grupp, clickData)



@app.callback([
    Output('x_scatter_grid', 'value'),
    Output('y_scatter_grid', 'value')],
    [Input('var', 'value')])
def scatterplot_options_grid(var):
    if len(var) == 1:
        return var[0], None
    if len(var) > 1:
        return var[0], var[1]



@app.callback(Output('scatterplot_div_grid', 'children'),
              [Input('x_scatter_grid', 'value'),
               Input('y_scatter_grid', 'value'),
               Input('checklist_scatter_grid', 'value'),
               Input('grupp', 'value'),
               Input('treemap', 'clickData')])
def scatterplot_grid_fig(x, y, checklist, aggregat, clickData):
    print("Scatterplot grid")
    return scatterplot_grid(x, y, checklist, aggregat, clickData)



@app.callback([
    Output('variabel_histogram_grid', 'value'),
    Input('var', 'value')])
def histogram_options_grid(var):
    return var

    

@app.callback(Output('histogram_div_grid', 'children'),
              [Input('variabel_histogram_grid', 'value'),
               Input('bins_histogram_grid', 'value'),
               Input('checklist_histogram_grid', 'value'),
               Input('grupp', 'value'),
               Input('treemap', 'clickData')])
def histogram_grid_fig(variabel, bins, checklist, aggregat, clickData):
    print("Histogram grid")
    return histogram_grid(variabel, bins, checklist, aggregat, clickData)



@app.callback([
    Output('variabel_boxplot_grid', 'value'),
    Input('var', 'value')])
def boxplot_options_grid(var):
    return var

    

@app.callback(Output('boxplot_div_grid', 'children'),
              [Input('variabel_boxplot_grid', 'value'),
              Input('boxpoints_boxplot_grid', 'value'),
              Input('checklist_boxplot_grid', 'value'),
              Input('grupp', 'value'),
              Input('treemap', 'clickData')])
def boxplot_grid_fig(variabel, boxpoints, checklist, aggregat, clickData):
    print("Boxplot grid")
    return boxplot_grid(variabel, boxpoints, checklist, aggregat, clickData)

@app.callback(Output("sammenligning", "children"),
              Input("slider", "value"))
def sammenligne_editert_ueditert(timestamp):
    return sammenlign_editert_ueditert(timestamp)


#########
# Plots #
#########
@app.callback(Output('bubble_div_side', 'children'),
              [Input('submit_table', 'n_clicks'),
               State('x', 'value'),
               State('y', 'value'),
               State('color', 'value'),
               State('values', 'value')])
def bubble_plot_side(n_click, x, y, color, values):
    return bubble_plt_side(n_click, x, y, color, values)


#########
# Enhet #
#########

@app.callback(Output('table3_enhet', 'data'),
              [
                  Input('var_foretak', 'value'),
                  #Input('var_enhet', 'value')
              ])
def enhetsdata_clb(org): # sett inn dette: , variabel. wtf
    return enhetstabell_store(org) # sett inn dette: , variabel. wtf

@app.callback(Output('enhetstabell1_div', 'children'),
              Input('submit_table_enhet', 'n_clicks'),
              Input('table3_enhet', 'data'),
              State('var_enhet', 'value'))
def enhetstabell_clb(n_clicks, data, var):
    return enhetstabell1(n_clicks, data, var)

@app.callback(Output('enhetsgraf_div', 'children'),
              Input('var_foretak', 'value'),
              Input('submit_table_enhet', 'n_clicks'))
def enhetsgraf1_clb(orgnrnavn, n_click):
    return enhet_plot(orgnrnavn, n_click)

"""
@app.callback(Output('enhetsgraf_div2', 'children'),
              Input('submit_table_enhet', 'n_clicks'),
              Input('editer_enhet', 'n_clicks'),
              Input('table3', 'data'),
              Input('table3', 'selected_columns'),
             State('var_enhet', 'value'))
def enhetsgraf2_clb(n_clicks, n_clicks_enhet, data, kol_ed, var):
    return enhet_plot_bar_var(n_clicks, n_clicks_enhet, data, kol_ed, var)
"""
@app.callback(Output('enhetsgraf_div2', 'children'),
              Output('enhetsgraf_div3', 'children'),
              Output('editer_enhet', 'n_clicks'),
              Input('table3', 'data'),
              Input('table3', 'selected_columns'),
              Input('editer_enhet', 'n_clicks'),
             State('var_enhet', 'value'),
             State('grupp_enhet', 'value'),
             State('var_foretak', 'value'))
def enhetsgraf3_clb(data, kol_ed, n_click, var, grupp, orgnrnavn):
    return enhet_plot_bar_agg(data, kol_ed, var, grupp, orgnrnavn, n_click)

@app.callback(
    [Output('table3', 'data')],
    [Output('table3', 'columns')],
    [Output('editer_enhet_godta', 'n_clicks')],
    [Input('editer_enhet_godta', 'n_clicks')],
    [Input('table3', 'data')],
    [Input('table3', 'selected_columns')],
    [State('table3', 'columns')])
def update_columns_clb(n_clicks, data, value, columns):
    print(dash.callback_context.inputs_list)
    return update_columns(n_clicks, data, value, columns)


# Offcanvas

@app.callback(
    Output("offcanvas", "is_open"),
    Input("offcanvas_knapp", "n_clicks"),
    State("offcanvas", "is_open"),
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open

@app.callback(
    Output("offcanvas", "children"),
    [
        Input('var_foretak', 'value')
    ]
)

def show_offcanvas_innhold(foretak):
    print(dash.callback_context.inputs_list)
    return offcanvas_innhold(foretak)


#####################
# Loggføringstabell #
#####################

@app.callback(
    Output('tabell_logg', 'children'),
    Input('url', 'pathname'))
def show_log_table(data):
    return logg_tabell(data)

#############
# Tidsserie #
#############

@app.callback(
    Output("tidsserie_figur", "children"),
    [
        Input("tid_aggregering", "value"),
        Input("tid_variable", "value")
    ]
)
def disp_time_series(agg, var):
    return display_time_series(agg, var)

##############
# Kontroller #
##############

@app.callback(
    Output('tabell_feilliste', 'children'),
    [
        Input('url', 'pathname'),
        Input('velg_feilliste', 'value')
    ]
)
def show_feilliste_table(data, feilliste):
    return feilliste_tabell(data, feilliste)

@app.callback(Output('tabell_feilliste', 'data'),
              [Input('godta_endring', 'n_clicks'),
              State('feilliste_tabell_endret','data')])

def oppdater_feilliste_clb(n_clicks, data):
    return oppdater_feilliste_db(data)


 
# Oppdaterer figuren på kontroller-siden (histogram med hjelpevar og hovedvar), basert på klikkdata fra tabell
@app.callback(
    Output('figur_feilliste_vars', 'children'),
    [
    Input("feilliste_tabell_endret", "active_cell"), 
    Input('feilliste_tabell_endret', 'derived_virtual_data'),
    Input('velg_feilliste', 'value')
    ]
)
def show_feilliste_figur(enhet_rad, tabelldata, feilliste):
    return model_feilliste_figur(enhet_rad, tabelldata, feilliste)


#Tabell for enhet på kontroll-side

@app.callback(Output('kontroll_tabell_enhet', 'data'),
              [
                  Input('dropdown_enhet', 'value'),
              ])
def kontroll_enhetsdata_clb(org):
    return kontroll_enhetstabell_store(org)

@app.callback(Output('kontroll_enhet_tabell_div', 'children'),
              Input('dropdown_enhet', 'value'),
              Input('kontroll_tabell_enhet', 'data'))
def kontroll_enhetstabell_clb(n_clicks, data):
    #print(dash.callback_context.inputs_list)
    return kontroll_enhetstabell(n_clicks, data)

@app.callback(
    [Output('kontroll_enhet_tabell', 'data')],
    [Output('kontroll_enhet_tabell', 'columns')],
    [Output('kontroll_editer_enhet_godta', 'n_clicks')],
    [Input('kontroll_editer_enhet_godta', 'n_clicks')],
    [Input('kontroll_enhet_tabell', 'data')],
    [Input('kontroll_enhet_tabell', 'selected_columns')],
    [State('kontroll_enhet_tabell', 'columns')])
def kontroll_update_columns_clb(n_clicks, data, value, columns):
    print(dash.callback_context.inputs_list)
    return kontroll_update_columns(n_clicks, data, value, columns)

# Offcanvas
@app.callback(
    Output("kontroll_offcanvas", "is_open"),
    Input("kontroll_offcanvas_knapp", "n_clicks"),
    State("kontroll_offcanvas", "is_open"),
)

def toggle_offcanvas(n1, is_open):
    print(dash.callback_context.inputs_list)
    if n1:
        return not is_open
    return is_open

@app.callback(
    Output("kontroll_offcanvas", "children"),
    [
        Input('dropdown_enhet', 'value')
    ]
)
def vis_kontroll_offcanvas_innhold(foretak):
    print(dash.callback_context.inputs_list)
    return kontroll_offcanvas_innhold(foretak)



if __name__ == '__main__':
    app.run_server(debug = True, port=2264)

