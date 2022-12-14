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
from models.models_enhet import enhetstabell1, enhet_plot, enhetstabell_store, update_columns, enhet_plot_bar_agg, offcanvas_innhold
from models.models_logg import logg_tabell
from models.models_kontroller import feilliste_tabell, innhent_feilliste, oppdater_feilliste_db, model_feilliste_figur, kontroll_enhetstabell_store, kontroll_update_columns, kontroll_enhetstabell, kontroll_offcanvas_innhold

from templates.homepage import Svarinngang
from templates.navbar import Navbar
from templates.grid import Grid
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

def get_callbacks(app):
    # Sidenavigasjon, fungerer sammen med templates/navbar.py
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
                   Input('treemap', 'clickData'),
                  Input('scatter_aggregat', 'value')])
    def scatterplot_grid_fig(x, y, checklist, aggregat, clickData, scatter_aggregat):
        return scatterplot_grid(x, y, checklist, aggregat, clickData, scatter_aggregat)



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
        return histogram_grid(variabel, bins, checklist, aggregat, clickData)



    @app.callback([
        Output('variabel_boxplot_grid', 'value'),
        Input('var', 'value')])
    def boxplot_options_grid(var):
        return var



    @app.callback(Output('boxplot_div_grid', 'children'),
                  [Input('variabel_boxplot_grid', 'value'),
                  #Input('boxpoints_boxplot_grid', 'value'), # Tas ut av funksjonen
                  Input('checklist_boxplot_grid', 'value'),
                  Input('grupp', 'value'),
                  Input('treemap', 'clickData')])
    def boxplot_grid_fig(variabel, checklist, aggregat, clickData): # Tatt ut av listen: boxpoints, 
        return boxplot_grid(variabel, checklist, aggregat, clickData) # Tatt ut av listen: boxpoints, 

    @app.callback(Output("sammenligning", "children"),
                  Input("slider", "value"))
    def sammenligne_editert_ueditert(timestamp):
        return sammenlign_editert_ueditert(timestamp)


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
    # Loggf??ringstabell #
    #####################

    @app.callback(
        Output('tabell_logg', 'children'),
        Input('url', 'pathname'))
    def show_log_table(data):
        return logg_tabell(data)

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



    # Oppdaterer figuren p?? kontroller-siden (histogram med hjelpevar og hovedvar), basert p?? klikkdata fra tabell
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


    #Tabell for enhet p?? kontroll-side
    @app.callback(Output('kontroll_tabell_enhet', 'data'),
                  [
                      Input('feilliste_tabell_endret', 'active_cell'),
                      Input('feilliste_tabell_endret', 'derived_virtual_data')
                  ])
    def kontroll_enhetsdata_clb(enhet_rad, tabelldata):
        return kontroll_enhetstabell_store(enhet_rad, tabelldata)



    @app.callback(Output('kontroll_enhet_tabell_div', 'children'),
                  [
                      Input('feilliste_tabell_endret', 'active_cell'),
                      Input('kontroll_tabell_enhet', 'data')
                  ])
    def kontroll_enhetstabell_clb(enhet_rad, data):
        #print(dash.callback_context.inputs_list)
        return kontroll_enhetstabell(enhet_rad, data)


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
            Input('feilliste_tabell_endret', 'active_cell'),
            Input('feilliste_tabell_endret', 'derived_virtual_data')
        ])
    def vis_kontroll_offcanvas_innhold(enhet_rad, tabelldata):
        print(dash.callback_context.inputs_list)
        return kontroll_offcanvas_innhold(enhet_rad, tabelldata)
