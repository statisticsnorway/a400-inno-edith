from models.models_delt import connect, cardify_figure, table # For å importere grunnfunksjonalitet fra den delte filen
conn, engine, db = connect() # Oppretter filstier som brukes i spørringer

import pandas as pd
import datetime as date
import numpy as np

import sqlite3

import json

import dash
import dash_core_components as dcc
from dash import no_update
from dash.exceptions import PreventUpdate
from flask import request # for brukernavn

import plotly.express as px


with open("config.json") as config:
    config = json.load(config)



def enhetstabell_store(org): # Sett inn dette , variabel
    print("Laster inn data")
    df = pd.read_sql(f"SELECT * FROM {config['tabeller']['raadata']} WHERE OrgnrNavn = '{org}'", con=engine)
    if False is True:# Denne må gjøres conditional på om editeringer eksisterer? 
        df_e = pd.read_sql(f"select * from editeringer WHERE orgnrNavn = '{org}'", con=engine) 
        df = pd.concat([df, df_e])
        df = df.sort_values(by="Log_tid", ascending=False)
        df = df.drop_duplicates(subset=["VARIABEL", "OrgnrNavn"], keep="first")
    data = df.to_dict('rows')
    columns = [{'name': i, 'id': i} for i in df.columns]
    return data #table(id = 'table3', data = data, columns = columns)



def enhetstabell1(n_clicks, data, var):
    perioder = {}
    for i in config["perioder"]: # Finnes sikkert en bedre løsning enn dette
        perioder[i] = config["perioder"][i]["år"] # Må kanskje finne en litt annen måte å gjøre det på hvis kobling av perioder skal skje i funksjonen
    if n_clicks:
        df = pd.DataFrame().from_dict(data)
        print(df.head())
        df = df[[config["id_variabel"], config["navn_variabel"], "VARIABEL"] + list(perioder.values())]
        try:
            if config["brukernavn"] != "":
                df["Editert_av"] = config["brukernavn"]
        except:
            try:
                df["Editert_av"] = request.authorization["username"]
            except:
                df["Editert_av"] = ""
        df["Kommentar"] = ""
        df = df[df['VARIABEL'].isin(var)]
        data = df.to_dict('rows')
        """ Definerer hvilke kolonner som skal være selekterbare, og hvilke som ikke skal være det """
        columns = [{'name': i, 'id': i, 'on_change': {'action': 'validate'}, 'selectable': True} if i in set([config["perioder"]["t"]["år"], 'Vekt']) 
            else {'name': i, 'id': i, 'editable': True} if i == "Kommentar" 
            else {'name': i, 'id': i} for i in df.columns]
        return table(id = 'table3', data = data, columns = columns, column_selectable="multi")
    else:
        no_update



def update_columns(n_clicks, data, value, columns):
    print("Update_columns starter")
    t = config["perioder"]["t"]["år"]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0] # Viser id-en som tilhører komponenten som utløste callbacken
    df = pd.DataFrame().from_dict(data)

    if value is None or columns is None: # Hindrer update dersom det ikke er skjedd endring i columns eller value
        raise PreventUpdate

    inColumns = any(c.get('id') == value for c in columns) # Finn ut hva dette er. Den er alltid false. Tror det er for å hindre chaining av append til columns så man slipper å få flere "_editert" kolonner
    print("inColumns")
    print(inColumns)
    if inColumns == True:
        raise PreventUpdate

    if value: # Value er hvilken kolonne som er selected
        for i in value:
            check = {'name': i+"_editert",'id': i+"_editert",'deletable': True, 'editable': True}
            if check not in columns: # Setter inn ny kolonne som heter value+_editert som man kan editere verdi i.
                columns.append({
                    'name': i+"_editert",
                    'id': i+"_editert",
                    'deletable': True,
                    'editable': True
                })
    #elif len(value) == 0: # Tror dette kan fjernes, kan ikke se noen nytte av det
    #    if "År_2019" not in value and "År_2019_editert" in list(df.columns):
    #        columns.remove({
    #            'name': "År_2019_editert",
    #            'id': "År_2019_editert",
    #            'deletable': True
    #        })

    #    elif "Vekt" not in value and "Vekt_editert" in list(df.columns):
    #        columns.remove({
    #            'name': "Vekt_editert",
    #            'id': "Vekt_editert",
    #            'deletable': True
    #        })
    if n_clicks: # Dette aktiveres bare hvis man har klikket på "Godta endringer" knappen
        if f'{config["perioder"]["t"]["år"]}_editert' in df.columns: # Sjekker at man har opprettet en "_editert" kolonne i tidligere steg
            for i in df.index: # Looper gjennom index til tabellen, sikrer at alle endrede verdier blir med om flere endres samtidig
                if pd.isna(df[config["perioder"]["t"]["år"] + "_editert"][i]) == False: # Sjekker om det finnes en editert verdi i en gitt kolonne
                    df.at[i,t] = df.loc[i][config["perioder"]["t"]["år"] + "_editert"]
                    oppdater_database(df.loc[[i]].reset_index()) # Oppdaterer til database, se egen funksjon. Ligger her sånn at endringer i dashbordet kun skjer hvis lagringen til databasen skjedde # OBS! Må ha med resetindex pga loc[0] i oppdater_database-funksjonen
            df.drop(columns = config["perioder"]["t"]["år"] + "_editert", inplace = True) # Dropper kolonnen med editerte verdier  slik at dashbordet tas tilbake til slik det var før man lagde en "_editert" kolonne(merk, den endrede verdien er nå lagret til tabellen for editeringer som er spesifisert i config.json)
        #elif 'Vekt_editert' in df.columns:
        #    df['Vekt'] = df['Vekt_editert']
        #    df.drop(columns = 'Vekt_editert', inplace = True)
        data = df.to_dict('rows')
        print(df.columns)
        columns = [{'name': i, 'id': i, 'on_change': {'action': 'validate'}, 'selectable': True} if i in set([config["perioder"]["t"]["år"], 'Vekt']) 
            else {'name': i, 'id': i, 'editable': True} if i == "Kommentar" # Gjør at man kan editere i kommentar kolonnen.
            else {'name': i, 'id': i} for i in df.columns] # Legger inn øvrige kolonner
        print("Update_columns avsluttes")
        return data, columns, None # Returnerer None til knappen, slik at du må faktisk trykke på knappen igjen for at denne funksjonen skal kunne utløses igjen.
    print("Update_columns avsluttes")
    return no_update, columns, None



def oppdater_database(df): # Funksjon for å lagre editering og loggføre bruker, kommentar og tidspunkt
    print("Starter lagring av editering og loggføring av data nedenfor")
    print("Dette er dataene fra tabellen:")
    print(df)
    print()
    conn, engine, db = connect() # Fra models_delt.py
    CursorObject = conn.cursor()
    enhet = df[config['id_variabel']].loc[0] # Brukes for å finne den spesifikke raden i datasettet som endres
    variabel = df['VARIABEL'].loc[0]
    data_som_endres = pd.read_sql(f"SELECT * from {config['tabeller']['raadata']} WHERE {config['id_variabel']} = '{enhet}' and VARIABEL ='{variabel}'", con=engine) # Leser inn hele raden med tidligere data
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

    """ Oppretter editeringer tabell hvis den ikke allerede eksisterer """
    tabeller = pd.read_sql("SELECT name FROM sqlite_master  WHERE type='table'", con=engine)
    if "editeringer" not in tabeller["name"].unique():
        c = conn.cursor()
        c.execute(f'''CREATE TABLE {config["tabeller"]["editeringer"]}({kolonner})''')
        conn.commit()

    """ Setter inn i editeringer tabellen """
    sqlite_insert_query = f"""INSERT INTO editeringer
            ({kolonner})
            VALUES
            ({antall})"""
    CursorObject.execute(sqlite_insert_query, data_som_endres.loc[0]) # Sikrer at kun riktig informasjon lagres
    conn.commit()
    CursorObject.close()
    print("Editering og loggføring lagret") # Bekreftelse i terminalen på at endringen ble skrevet



def enhet_plot(orgnrnavn, n_clicks): # Nøkkeltall
    print("Lager nøkkeltall-plot på enhetssiden")
    perioder = ""
    for i in config["perioder"]: # Finnes sikkert en bedre løsning enn dette
        perioder = perioder + str(config["perioder"][i]["år"]) + str(", ")
    perioder = perioder[:-2] # fjerner siste ", " så listen blir riktig
    if n_clicks:
        variabler = config["nøkkeltall_enhetssiden"]
        df = pd.read_sql(f"SELECT VARIABEL, {perioder} FROM {config['tabeller']['raadata']} WHERE OrgNrNavn = '{orgnrnavn}' and VARIABEL in {tuple(variabler)}", con=engine)
        # Start - midlertidig fiks på feil datatype i kolonne. Fjernes når kolonner har riktig verdi i sqlite
        perioder = []
        for i in config["perioder"]:
            perioder = perioder + [config["perioder"][i]["år"]]
        df[perioder] = df[perioder].astype("float")
        # Slutt - midlertidig fiks på feil datatype i kolonne. Fjernes når kolonner har riktig verdi i sqlite
        df = df.melt(id_vars=["VARIABEL"], var_name="År", value_name="Verdi").sort_values(["VARIABEL", "År"]) # Sorteres for å kunne regne prosentdifferanser
        if len(config["perioder"]) > 1:            
            for i in variabler:
                df.loc[df["VARIABEL"] == i, "diff"] = (round(df["Verdi"].pct_change(), 3)*100).map("{:,.1f}%".format)
                print(df.loc[df["VARIABEL"] == i].head())
        """ Lager figur """
        fig = px.bar(
            df, 
            x="År", 
            y="Verdi",
            #text = "diff", # Bare hvis len > 1
            barmode = "group", 
            title="Nøkkeltall", 
            facet_col="VARIABEL", 
            facet_col_spacing=0.04, 
            facet_row_spacing=0.04
        )
        fig.update_yaxes(matches=None, showticklabels=True)
        fig.update_layout(bargap=0.2,margin=dict(t=150))
        graph = dcc.Graph(id = 'enhet_bar_topp', figure = fig)
        return graph



def enhet_plot_bar_agg(data, kol_ed, var, grupp, orgnrnavn, n_clicks):
    print("Starter av enhet_plot_bar_agg")
    temp_dict = {}
    for i in config["perioder"]: # Finnes sikkert en bedre løsning enn dette
        temp_dict[i] = config["perioder"][i]["år"] # Må kanskje finne en litt annen måte å gjøre det på hvis kobling av perioder skal skje i funksjonen
    """ Laster inn data """
    if len(var) == 1:
        grupp_var = pd.read_sql(f"SELECT {grupp} FROM {config['tabeller']['raadata']} WHERE OrgNrNavn = '{orgnrnavn}' and VARIABEL = '{var[0]}'", con=engine).loc[0,grupp]
        df_grupp = pd.read_sql(f"SELECT VARIABEL, SUM({t_2}) {t_2}, SUM({t_1}) {t_1}, SUM({t}) {t}, {grupp} FROM {config['tabeller']['raadata']} WHERE {grupp} = '{grupp_var}' and VARIABEL = '{var[0]}' and OrgnrNavn NOT IN ('{orgnrnavn}') GROUP BY VARIABEL", con=engine)
    else: # Hvis var er mer enn ett element må det skrives som en tuple i SQL spørringen
        grupp_var = pd.read_sql(f"SELECT {grupp} FROM {config['tabeller']['raadata']} WHERE OrgNrNavn = '{orgnrnavn}' and VARIABEL IN {tuple(var)}", con=engine).loc[0,grupp]
        df_grupp = pd.read_sql(f"SELECT VARIABEL, SUM({t_2}) {t_2}, SUM({t_1}) {t_1}, SUM({t}) {t}, {grupp} FROM {config['tabeller']['raadata']} WHERE {grupp} = '{grupp_var}' and VARIABEL IN {tuple(var)} and OrgnrNavn NOT IN ('{orgnrnavn}') GROUP BY VARIABEL", con=engine)
    df = pd.DataFrame().from_dict(data)
    """ Tilpasser data for visualisering """
    df["Enhet"] = df["Navn"]
    df_grupp["Enhet"] = "Andre"
    kolonner = ["Enhet", "VARIABEL", t_2, t_1, t]
    if n_clicks:
        if code["perioder"][0]["t"][0]["år"] + "_editert" in df.columns:
            kolonner = kolonner+[code["perioder"][0]["t"][0]["år"] + "_editert"]
            df_grupp[code["perioder"][0]["t"][0]["år"] + "_editert"] = df_grupp[t]
    df = df[kolonner]
    df_grupp = df_grupp[kolonner]
    df1 = df.melt(id_vars=["VARIABEL", "Enhet"], var_name="År", value_name="value")
    df2 = df_grupp.melt(id_vars=["VARIABEL", "Enhet"], var_name="År", value_name="value")
    df_merge = pd.concat([df1, df2])

    """ Lager figurer """
    fig1 = px.bar(df1, x="År", y="value", barmode = "group", title="Utvikling over tid", facet_col="VARIABEL", category_orders={"VARIABEL": var},facet_col_spacing=0.04, facet_row_spacing=0.04)
    fig1.update_yaxes(matches=None, showticklabels=True)
    fig1.update_layout(bargap=0.2,margin=dict(t=150))
    graph1 = dcc.Graph(id = 'enhet_bar_var', figure = fig1)
    fig2 = px.bar(df_merge,x="value",y="År",orientation="h",color="Enhet",barmode="stack",facet_col="VARIABEL", title=str(grupp)+" "+str(grupp_var))
    fig2.update_xaxes(matches=None, showticklabels=True)
    fig2.update_layout(bargap=0.2,margin=dict(t=150))
    graph2 = dcc.Graph(id = 'enhet_bar_var', figure = fig2)
    return graph1, graph2, None

def offcanvas_innhold(foretak):
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

print("models_enhet.py lastet")