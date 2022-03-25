from models.models_delt import connect, cardify_figure, table # For å importere grunnfunksjonalitet fra den delte filen
conn, engine, db = connect() # Oppretter filstier som brukes i spørringer

import pandas as pd
import numpy as np

import dash
import dash_core_components as dcc
from dash import no_update
from dash.exceptions import PreventUpdate
import dash_html_components as html

import plotly.express as px

import dash_table as dt

import json
with open("config.json") as config:
    config = json.load(config)
    
with open("variabler.json") as variabler:
    config_variabler = json.load(variabler)
    
    
import sqlite3
from sqlalchemy import create_engine
import datetime as date
from flask import request # for brukernavn

'''
@app.callback(
    Output('tabell_feilliste', 'children'),
    Input('url', 'pathname'))
'''

def innhent_feilliste(liste):
    #Leser inn fil
    print('Leser csv')
    print(liste)
    df = pd.read_csv(config['data']['filsti'] + "/feillister_test2.csv", ';')
    df['feilliste'] = df['feilliste'].str.replace(',', '') #Tar bort eventuelle komma i feilliste-kolonnen da det ikke funker med dropdown
    
    #Tar bort kommentarkolonnen som er lagret i databasen hvis det ikke ligger inne en tabell fra inneværende statistikkår
    t = config["perioder"]["t"]["år"][3:8]
    df['orgnr'] = df['orgnr'].astype(object).astype(str)
    
    if 'feilliste_kommentar' + t in pd.read_sql('SELECT name from sqlite_master where type= "table"', con=engine)['name'].tolist():
        df = df.drop("kommentar", axis = 1)
        print('Kommentar hentes fra db')
    
    #Henter kommentarkolonnen fra databasen
        feilliste_kommentar = pd.read_sql(f"SELECT * from feilliste_kommentar{t} WHERE kommentar IS NOT NULL", con=engine)
        
        df = pd.merge(df, feilliste_kommentar, how = "left", on = ['feilliste','orgnr'])
        cols = df.columns.drop('kommentar').tolist()
        df = df[['kommentar'] + cols]
    else:
        #Kommentarer lastes inn i databasen
        feillister_kommentar = df[['kommentar','feilliste','orgnr']]
        feillister_kommentar.to_sql('feilliste_kommentar' + t, con = engine, if_exists = 'append', chunksize = None)
    
    #Bearbeider og fikser variabeltyper
    df = df.replace(r'^\.$', np.nan, regex = True)
    df = df.apply(pd.to_numeric, errors= 'ignore')
    df_str = df.select_dtypes(include = ['object'])
    
    col_list = []
    for col in df_str.columns:
        if (True in list(df_str[col].str.contains('[A-Za-z]', regex = True))) is False:
            col_list.append(col)
    df[col_list] = df[col_list].replace(',', '.', regex=True).astype(float)
    df['orgnr'] = df['orgnr'].astype(object).astype(str)
    df['kommentar'] = df['kommentar'].fillna('.') #fyller inn for å gjøre det mulig å filtrere bort de som er sjekket
   
    print(df.head())
    #Avhengig av hvilken liste som velges i dropdown hentes variabler
    if "Alle" not in liste:
        feilliste_vars = df[df['feilliste'].isin(liste)].dropna(axis = 1, how = 'all').columns #Kolonnene hvor alle radene er NAN utelukkes
        print(feilliste_vars)
        valgt_feilliste = df.loc[df['feilliste'].isin(liste), feilliste_vars] #Kun rader som gjelder for feilliste + variablene relevant for liste
    else:
        valgt_feilliste = df
    return valgt_feilliste

def feilliste_tabell(url, valgt_feilliste):
    print('Henter feillister')
    df = innhent_feilliste(valgt_feilliste)

    data = df.to_dict('records')
    columns = [{'name': i, 'id': i}
              if i == "org_nr" or i == "orgnr" or i == "nace07" or i == "feilliste"
              else {'name': i, 'id': i, "editable": True} if i == "kommentar"
              else {"name": i, "id": i, "hideable": True}
              for i in df.columns]
    
    return dt.DataTable(
            id = 'feilliste_tabell_endret',
            style_cell={'textAlign': 'left', 'minWidth': '100px'},
            sort_action='native',
            data = data,
            columns = columns,
            filter_action='native',
            page_action = 'native',
            page_size = 20,
            sort_mode = 'single',
            #row_selectable = 'single', #Fungerer foreløpig ikke sammen med dropdown
            selected_rows=[],
            selected_row_ids = [],
       )


# Oppdaterer historgrammene på kontroll-siden

def model_feilliste_figur(enhet_rad, tabelldata,feilliste):
    if enhet_rad and feilliste:
        print('Lager feilliste figur')
        print("Valgt rad: ", enhet_rad)
        
        # Henter ut orgnr basert på valgt rad (celle som er klikket på)
        valgt_rad     = tabelldata[enhet_rad["row"]]
        enhet_klikket = valgt_rad["orgnr"]
        print("Valgt enhet: ",enhet_klikket)
        
        # Henter fra delreg basert på valgt orgnr. ---
        df_enhet = pd.read_sql(f"SELECT * FROM {config['tabeller']['raadata']} WHERE Orgnr = '{enhet_klikket}'", con=engine)
        
        print(df_enhet)
        # Finner variablene i delreg.---
        options_vars = df_enhet['VARIABEL'].unique().tolist()
        print(options_vars)
        
        # Finner variablene i valgt feilliste ---
        feilliste_valgt = feilliste
        df_feilliste = pd.read_csv(config['data']['filsti'] + "/feillister_test2.csv", ';')
        df_feilliste['feilliste'] = df_feilliste['feilliste'].str.replace(',', '')
        df_feilliste_valgt = df_feilliste[df_feilliste['feilliste'].isin(feilliste)]
        df_feilliste_valgt = df_feilliste_valgt.dropna(axis=1, how = 'all')
        feilliste_vars = df_feilliste_valgt.columns.tolist()
        feilliste_vars = [feilliste_vars.upper() for feilliste_vars in feilliste_vars] #Variabler har store bokstaver i appen
        
        # Finner relevante variable for figuren
        relevant_vars = list(set(feilliste_vars).intersection(options_vars))
        
        # Plukker ut disse variablene fra delreg.
        df_enhet_relevant_vars = df_enhet[df_enhet['VARIABEL'].isin(relevant_vars)]
        # Omformaterer
        perioder = {} # Finnes sikkert en bedre løsning enn dette
        for i in config["perioder"]:
            perioder[i] = config["perioder"][i]["år"]
        df_enhet_relevant_vars = df_enhet_relevant_vars[["VARIABEL"] + list(perioder.values())]
        df_enhet_relevant_vars = df_enhet_relevant_vars.melt(id_vars=["VARIABEL"], var_name="År", value_name="Verdi").sort_values(["VARIABEL", "År"])
        df_enhet_relevant_vars['Verdi'] = df_enhet_relevant_vars['Verdi'].str.replace(',', '').astype(float)

        print(df_enhet_relevant_vars)

        fig1 = px.bar(df_enhet_relevant_vars, 
                      x="År", y="Verdi",
                      barmode = "group",
                      facet_col = "VARIABEL",
                      facet_col_spacing=0.04, 
                      facet_row_spacing=0.04
                     )
        fig1.update_yaxes(matches=None, showticklabels=True)
        fig1.update_layout(bargap=0.2,margin=dict(t=150))
        fig_feilliste_var = dcc.Graph(id = 'xxx', figure = fig1)
        return fig_feilliste_var


def oppdater_feilliste_db(data):  
    t = config["perioder"]["t"]["år"][3:8]
    df = pd.DataFrame().from_dict(data)
    print(df.head())
    if 'feilliste' in df: #Bare for å teste om det ikke er en tom df
        feillister_kommentar = df[['kommentar','feilliste','orgnr']]
        
         #For å unngå at radene forsvinner etter at man subsetter på feilliste blir radene "appended" og dubletter fjernes etterpå
        feillister_kommentar.to_sql('feilliste_kommentar' + t, con = engine, if_exists = 'append', chunksize = None)
        pd.read_sql(f"SELECT * from feilliste_kommentar{t} WHERE kommentar IS NOT NULL", con=engine).drop('index', axis = 1).drop_duplicates(subset = ['orgnr', 'feilliste'], keep='last').to_sql('feilliste_kommentar' + t, con = engine, if_exists = 'replace')


'''
@app.callback(Output('kontroll_tabell_enhet', 'data'),
              [
                  Input('dropdown_enhet', 'value'),
              ])
'''

def kontroll_enhetstabell_store(org): # Sett inn dette , variabel
    #if org:
    #org = org[0:9]
    print("enhetstabell_store")
    print(org)
    variabler = tuple(config_variabler["variabler"])
    print(variabler)
    #df = pd.read_sql(f"SELECT * FROM {config['tabeller']['raadata']} WHERE OrgnrNavn = '{org}'", con=engine)
    df = pd.read_sql(f"SELECT * FROM {config['tabeller']['raadata']} WHERE OrgnrNavn = '{org}' AND Variabel IN {variabler}", con=engine)
    print(df.head())
    if False is True:# Denne må gjøres conditional på om editeringer eksisterer? 
        df_e = pd.read_sql(f"select * from editeringer WHERE orgnrNavn = '{org}'", con=engine) 

        print(df_e.head())
        df = pd.concat([df, df_e])
        df = df.sort_values(by="Log_tid", ascending=False)
        df = df.drop_duplicates(subset=["VARIABEL", "OrgnrNavn"], keep="first")
        print(df)
    data = df.to_dict('rows')
    columns = [{'name': i, 'id': i} for i in df.columns]
    return data #table(id = 'table3', data = data, columns = columns)

'''
@app.callback(Output('kontroll_enhet_tabell_div', 'children'),
              Input('dropdown_enhet', 'value'),
              Input('kontroll_tabell_enhet', 'data'))
'''

def kontroll_enhetstabell(n_clicks, data):
    perioder = {}
    for i in config["perioder"]: # Finnes sikkert en bedre løsning enn dette
        perioder[i] = config["perioder"][i]["år"] # Må kanskje finne en litt annen måte å gjøre det på hvis kobling av perioder skal skje i funksjonen
    if n_clicks:
        df = pd.DataFrame().from_dict(data)
        print("enhetstabell")
        print(df.head())
        df = df[[config["id_variabel"], config["navn_variabel"], "VARIABEL"] + list(perioder.values())]
        df["Editert_av"] = request.authorization["username"]
        df["Kommentar"] = ""
        df = df.dropna(subset=[config["perioder"]["t"]["år"], config["perioder"]["t-1"]["år"], config["perioder"]["t-2"]["år"]]).drop_duplicates().reset_index(drop=True)
        data = df.to_dict('rows')
        """ Definerer hvilke kolonner som skal være selekterbare, og hvilke som ikke skal være det """
        columns = [{'name': i, 'id': i, 'on_change': {'action': 'validate'}, 'selectable': True} if i in set([config["perioder"]["t"]["år"], 'Vekt']) 
            else {'name': i, 'id': i, 'editable': True} if i == "Kommentar" 
            else {'name': i, 'id': i} for i in df.columns]
        return table(id = 'kontroll_enhet_tabell', data = data, columns = columns, column_selectable="multi")
    else:
        no_update
        
'''
@app.callback(
    [Output('kontroll_enhet_tabell', 'data')],
    [Output('kontroll_enhet_tabell', 'columns')],
    [Output('kontroll_editer_enhet_godta', 'n_clicks')],
    [Input('kontroll_editer_enhet_godta', 'n_clicks')],
    [Input('kontroll_enhet_tabell', 'data')],
    [Input('kontroll_enhet_tabell', 'selected_columns')],
    [State('kontroll_enhet_tabell', 'columns')])        
'''    
        
def kontroll_update_columns(n_clicks, data, value, columns):
    print("Update_columns starter")
    t = config["perioder"]["t"]["år"]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    df = pd.DataFrame().from_dict(data)

    if value is None or columns is None:
        raise PreventUpdate

    inColumns = any(c.get('id') == value for c in columns) # Finn ut hva dette er
    if inColumns == True:
        raise PreventUpdate

    if value:
        for i in value:
            check = {'name': i+"_editert",'id': i+"_editert",'deletable': True, 'editable': True}
            if check not in columns:
                columns.append({
                    'name': i+"_editert",
                    'id': i+"_editert",
                    'deletable': True,
                    'editable': True
                })

    if n_clicks: # Dette aktiveres bare hvis man har klikket på "Godta endringer" knappen
        if f'{config["perioder"]["t"]["år"]}_editert' in df.columns:
            print(df.columns)
            print(df.head(1))
            for i in df.index: # Looper gjennom index til tabellen, sikrer at alle endrede verdier blir med om flere endres samtidig
                if pd.isna(df[config["perioder"]["t"]["år"] + "_editert"][i]) == False and pd.isna(df['Kommentar'][i]) == False: # Sjekker om det finnes en editert verdi
                    print("editert verdi")
                    df.at[i,t] = df.loc[i][config["perioder"]["t"]["år"] + "_editert"]
                    print(df.at[i,t])
                    oppdater_database(df.loc[[i]].reset_index()) # Oppdaterer til database, se egen funksjon. Ligger her sånn at endringer i dashbordet kun skjer hvis lagringen til databasen skjedde # OBS! Må ha med resetindex pga loc[0] i funksjonen
            df.drop(columns = config["perioder"]["t"]["år"] + "_editert", inplace = True)
        data = df.to_dict('rows')
        print(df.columns)
        columns = [{'name': i, 'id': i, 'on_change': {'action': 'validate'}, 'selectable': True} if i in set([config["perioder"]["t"]["år"], 'Vekt']) 
            else {'name': i, 'id': i, 'editable': True} if i == "Kommentar" 
            else {'name': i, 'id': i} for i in df.columns]
        print("Update_columns avsluttes")
        return data, columns, None # Returnerer None til knappen, slik at du må faktisk trykke på knappen igjen for at denne funksjonen skal kunne utløses igjen.
    print("Update_columns avsluttes")
    return no_update, columns, None



def oppdater_database(df): # Funksjon for å lagre editering og loggføre bruker, kommentar og tidspunkt
    print("Starter lagring av editering og loggføring av data nedenfor")
    print("Dette er dataene fra tabellen:")

    conn, engine, db = connect() # Fra models_delt.py
    CursorObject = conn.cursor()
    enhet = df[config['id_variabel']].loc[0] # Brukes for å finne den spesifikke raden i datasettet som endres
    variabel = df['VARIABEL'].loc[0]
    data_som_endres = pd.read_sql(f"SELECT * from {config['tabeller']['raadata']} WHERE {config['id_variabel']} = '{enhet}' and Variabel ='{variabel}'", con=engine) # Leser inn hele raden med tidligere data
    #del data_som_endres['index'] # Fjerner unødvendige kolonner
    data_som_endres['Editert_av'] = df['Editert_av'].loc[0] # Henter info om hvem som editerte fra Edith sin tabell
    data_som_endres['Kommentar'] = df['Kommentar'].loc[0] # Henter kommentaren som ble lagt inn i Edith sin tabell
    data_som_endres['Log_tid'] = date.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Legger til kolonne med tidsstempel
    """ Lagrer tidligere verdi før den overskrives for periode t """
    data_som_endres["Tidligere_verdi"] = data_som_endres[config["perioder"]["t"]["år"]]
    data_som_endres[config["perioder"]["t"]["år"]] = float(df[config["perioder"]["t"]["år"]].loc[0]) # Å definere det som float() gjør at det ikke blir til bytes i sql databasen
    print("Dette skal committes til editeringer")
    print(data_som_endres)
    
    """ Lager strings for SQL insert slik at det blir riktige kolonnenavn og riktig antall kolonner """
    # Midlertidig start
    del data_som_endres["index"]
    # Midlertidig slutt
    kolonner = ""
    for i in data_som_endres.columns: # Finnes sikkert en bedre løsning enn dette
        kolonner = kolonner + str(i) + str(", ")
    kolonner = kolonner[:-2] # fjerner siste ", " så listen blir riktig
    antall = ""
    for i in range(len(data_som_endres.columns)):
        antall = antall + str("?,")
    antall = antall[:-1] # fjerner siste "," så listen blir riktig
    print(kolonner)
    print(antall)
    
    """ Setter inn i editeringer tabellen """
    sqlite_insert_query = f"""INSERT INTO editeringer
            ({kolonner})
            VALUES
            ({antall})"""
    CursorObject.execute(sqlite_insert_query, data_som_endres.loc[0]) # Sikrer at kun riktig informasjon lagres
    conn.commit()
    CursorObject.close()
    print("Editering og loggføring lagret") # Bekreftelse i terminalen på at endringen ble skrevet
    
    
def kontroll_offcanvas_innhold(foretak):
    if foretak:
        print("Henter metadata og kommentarer til sidebar")
        metadata = tuple(config_variabler["metadatavariabler"])
        print(metadata)
        #df = pd.read_sql(f'SELECT Kommentar FROM {config["tabeller"]["editeringer"]} WHERE ORGNR = {str(foretak)[:9]}', con=engine)
        df = pd.read_sql(f'SELECT Variabel, {config["perioder"]["t"]["år"]}  AS VERDI FROM {config["tabeller"]["raadata"]} WHERE ORGNR = {str(foretak)[:9]} AND Variabel IN {metadata}', con=engine).drop_duplicates()
        print(df)
        data = df.to_dict("rows")
        columns = [{'name': i, 'id': i} for i in df.columns]
        print(data)
        return dt.DataTable(
                style_as_list_view = True,
                style_cell = {'textAlign': 'left'},
                style_data = {
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                data = data,
                columns = columns), html.P(), html.P("Kan lukkes ved å trykke på Esc")    


def main():
    print("Sett inn tester her")

if __name__ == "__main__":
    main()
print("models_kontroller.py lastet")