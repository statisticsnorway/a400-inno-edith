from models.models_delt import connect, cardify_figure, table # For å importere grunnfunksjonalitet fra den delte filen
conn, engine, db = connect() # Oppretter filstier som brukes i spørringer

from dash.exceptions import PreventUpdate # Vet ikke om denne trengs
from dash import no_update
import dash_html_components as html
import dash_core_components as dcc

import pandas as pd
import numpy as np

import json

import plotly.express as px
import plotly.graph_objects as go

import time
from datetime import datetime
from datetime import timedelta

with open("config.json") as config: # Laster in valg fra config.json
    config = json.load(config)



def treeplot(n_click, var, grupp):
    if n_click:
        if len(var) == 1:
            df = pd.read_sql(f'SELECT * FROM {config["tabeller"]["raadata"]} WHERE VARIABEL in ("{var[0]}")', con=engine)
        if len(var) > 1:
            df = pd.read_sql(f"SELECT * FROM {config['tabeller']['raadata']} WHERE VARIABEL in {tuple(var)}", con=engine)
        df = df.fillna(np.nan)
        fig = px.treemap(df, path = grupp , values = config["perioder"]["t"]["år"])
        graph = dcc.Graph(id = 'treemap', figure = fig)
        data = df.to_dict('rows')
        return graph, data
    else:
        return no_update


def table_grid(data, grupp, clickData):
    df = pd.DataFrame(data)
    """ Forbereder lister over kolonner som skal være med videre, etter hvorvidt de er string/objekter eller numeriske kolonner """
    perioder = {}
    for i in config["perioder"]: # Finnes sikkert en bedre løsning enn dette
        perioder[i] = config["perioder"][i]["år"] # Må kanskje finne en litt annen måte å gjøre det på hvis kobling av perioder skal skje i funksjonen
#    str_cols = [config["id_variabel"], config["navn_variabel"], "Variabel"] # Kolonner til tabellen
    str_cols = [config["kombinert_id_navn"], "VARIABEL"]
    num_cols = list(perioder.values())
    """ Setter korrekt datatype til hver kolonne """
    df[grupp] = df[grupp].astype("object") # Sikrer at det er riktig datatype på kolonnene
    df[str_cols] = df[str_cols].astype("object") # Sikrer at det er riktig datatype på kolonnene
    df[num_cols] = df[num_cols].astype("float") # Sikrer at det er riktig datatype på kolonnene
    """ Regner ut differanser mellom år dersom det er mer enn 1 periode definert i config """
    if len(config["perioder"]) > 1:
        num_cols = []
        for i in range(len(config["perioder"])):
            a = config["perioder"][list(config["perioder"].keys())[i]]["år"]
            num_cols.append(a)
            try:
                b = config["perioder"][list(config["perioder"].keys())[i+1]]["år"]
                c = config["perioder"][list(config["perioder"].keys())[i]]["år_til_år"]
                df[c] = df[a] - df[b]
                num_cols.append(c)
            except:
                print("Ferdig med beregning av diff")
    else:
        print("Ingen beregning av diff")

    """ clickData håndtering """
    """ Finner ut hvilket nivå clickdata fra treemap peker til """
    nivå = None
    if clickData == None: # Er det ingen clickdata er man på øverste nivå, fordi man ikke har drillet nedover.
        nivå = "topp"
    else: # Eksisterer clickData så sjekkes innholdet mer
        if "id" in clickData["points"][0]:
            aggregater = clickData["points"][0]["id"].split("/") # Siden id variabelen er en string med hvilke verdier man har klikket på separert med / gjøres det om til en liste
            if "entry" not in clickData["points"][0]: # Iblant bugger clickData seg ut om du klikker deg opp igjen for fort
                aggregater = aggregater[:-1] # Løses vanligvis med at siste aggregat droppes fra listen
            elif clickData["points"][0]["entry"] == aggregater[-1]: # Du kan klikke deg oppover ved å klikke på samme rute som du klikket inn i, derfor viktig å sjekke om entry-point er samme rute som nederste aggregat i listen
                aggregater = aggregater[:-1]
            if len(aggregater) == len(grupp): # Sjekker om man er på nederste nivå
                nivå = "enhet"
        else:
            nivå = "topp" # Hvis id ikke er i clickData så har man sannsynligvis navigert seg til toppen igjen

    """ Lager riktig data til tabellen """
    if nivå != "topp":
        for i in range(len(aggregater)): # Looper gjennom en filtrering 1 gang per nivå
            df = df.loc[df[grupp[i]] == aggregater[i]]
    df = df[grupp + str_cols + num_cols]
    if nivå != "enhet": # Så lenge det ikke er på enhetsnivå så skal det aggregeres
        df = df.groupby(grupp+["VARIABEL"]).agg({i : "sum" for i in num_cols}).reset_index()
    """ Gjør data fra dataframe klart til dash table """
    data = df.to_dict("rows")
    columns = [{'name': i, 'id': i} for i in df.columns]
    return table(id = "tabell_grid", data = data, columns = columns)



def scatterplot_grid(x, y, checklist, aggregat, clickData):
    tilpasning_til_spørring = ""
    variabel_filter = f"WHERE VARIABEL in {tuple([x]+[y])} "
    tilpasning_til_spørring = tilpasning_til_spørring + variabel_filter

    if clickData != None:
        if "entry" in clickData["points"][0]:
            aggregering_filter = "" # Skal bruke denne for å lage en SQL spørring som en string for å filtrere datasettet
            for i in range(len(clickData["points"][0]["id"].split("/"))): # Splitter clickdata sin id basert på / 
                aggregering_filter = aggregering_filter \
                + "AND " \
                + str(aggregat[i]) \
                + " = '" \
                + str(clickData["points"][0]["id"].split("/")[i]) \
                + "' " # \ på slutten er bare for å markere linjeskifte, gjør koden som lager stringen bittelitt mer leselig
            tilpasning_til_spørring = tilpasning_til_spørring + aggregering_filter
    spørring = f"SELECT * FROM {config['tabeller']['raadata']} " + tilpasning_til_spørring
    df = pd.read_sql(spørring, con = engine)
    df = df.loc[(df["VARIABEL"].isin([x, y]))].drop_duplicates(subset=["orgnrNavn", "VARIABEL"], keep="last")
    df = df.pivot(index = "orgnrNavn", columns=["VARIABEL"], values = config["perioder"]["t"]["år"])
    df = df[[x, y]].astype(float)
    if checklist != None: # Checklist starter som None
        if len(checklist) != 0: # Hvis man har krysset av er lengde mer enn 0
            df = df.loc[df[x] > 0]
            df = df.loc[df[y] > 0]
    fig = px.scatter(df,x = x,y = y, hover_name = df.index, trendline="ols")
    return dcc.Graph(id = "scatter_grid",figure=fig)



def histogram_grid(variabel, bins, checklist, aggregat, clickData):
    tilpasning_til_spørring = ""
    variabel_filter = f"WHERE VARIABEL = '{variabel}' "
    tilpasning_til_spørring = tilpasning_til_spørring + variabel_filter

    if clickData != None:
        if "id" in clickData["points"][0]:
            aggregering_filter = "" # Skal bruke denne for å lage en SQL spørring som en string for å filtrere datasettet
            for i in range(len(clickData["points"][0]["id"].split("/"))): # Splitter clickdata sin id basert på / 
                aggregering_filter = aggregering_filter \
                + "AND " \
                + str(aggregat[i]) \
                + " = '" \
                + str(clickData["points"][0]["id"].split("/")[i]) \
                + "' " # \ på slutten er bare for å markere linjeskifte, gjør koden som lager stringen bittelitt mer leselig
            tilpasning_til_spørring = tilpasning_til_spørring + aggregering_filter
    spørring = f"SELECT * FROM {config['tabeller']['raadata']} " + tilpasning_til_spørring
    df = pd.read_sql(spørring, con = engine)
    
    for i in config["perioder"]:
        df[config["perioder"][i]["år"]] = df[config["perioder"][i]["år"]].astype(float)
    if checklist != None: # Checklist starter som None
        if len(checklist) != 0: # Hvis man har krysset av er lengde mer enn 0
            df = df.loc[df[config["perioder"]["t"]["år"]] > 0]
    fig = go.Figure()
    for i in config["perioder"]: # Lager ett trace per årgang
        fig.add_trace(go.Histogram(
            x = df[config["perioder"][i]["år"]],
            histfunc = "count",
            histnorm = '',
            nbinsx = bins,
            name = config["perioder"][i]["år"]
        ))
    fig.update_layout(barmode = "group")
    return dcc.Graph(id = "histogram_grid", figure = fig)



def boxplot_grid(variabel, checklist, aggregat, clickData): # Tatt ut av listen: boxpoints, 
    print("Laster data til boxplot grid")
    tilpasning_til_spørring = ""
    variabel_filter = f"WHERE VARIABEL = '{variabel}' "
    tilpasning_til_spørring = tilpasning_til_spørring + variabel_filter

    if clickData != None:
        if "id" in clickData["points"][0]:
            aggregering_filter = "" # Skal bruke denne for å lage en SQL spørring som en string for å filtrere datasettet
            for i in range(len(clickData["points"][0]["id"].split("/"))): # Splitter clickdata sin id basert på / 
                aggregering_filter = aggregering_filter \
                + "AND " \
                + str(aggregat[i]) \
                + " = '" \
                + str(clickData["points"][0]["id"].split("/")[i]) \
                + "' " # \ på slutten er bare for å markere linjeskifte, gjør koden som lager stringen bittelitt mer leselig
            tilpasning_til_spørring = tilpasning_til_spørring + aggregering_filter
    spørring = f"SELECT * FROM {config['tabeller']['raadata']} " + tilpasning_til_spørring
    df = pd.read_sql(spørring, con = engine)
    print("Bearbeider data for boxplot grid")
    for i in config["perioder"]:
        df[config["perioder"][i]["år"]] = df[config["perioder"][i]["år"]].astype(float)
    if checklist != None: # Checklist starter som None
        if len(checklist) != 0: # Hvis man har krysset av er lengde mer enn 0
            df = df.loc[df[config["perioder"]["t"]["år"]] > 0]
    fig = go.Figure()
    print("Lager figur for boxplot grid")
    for i in config["perioder"]:# Lager ett trace per årgang
        fig.add_trace(go.Box(
            y=df[config["perioder"][i]["år"]],
            name=str(config["perioder"][i]["år"]),
            boxpoints = "all", # boxpoints, # Koblet til dropdown for outliers, foreløpig fungerer den ikke så den kommenteres ut
            text = df['orgnrNavn'],
#            marker=dict(
#                color='rgb(8,81,156)',
#                outliercolor='rgba(219, 64, 82, 0.6)',
#                line=dict(
#                    outliercolor='rgba(219, 64, 82, 0.6)',
#                    outlierwidth=2)),
#            line_color='rgb(8,81,156)'
        ))
    fig.update_layout(
        xaxis_title = "Periode",
        yaxis_title = variabel
    )
    return dcc.Graph(id = "boxplot_grid", figure = fig)


def sammenlign_editert_ueditert(timestamp):
    print("Sammenligne")
    aggregat = "ORG_FORM"
    variabel = "INTFOU"
    print("Sammenligne1")
    df_editert = pd.read_sql(f'SELECT * FROM {config["tabeller"]["editeringer"]}', con=engine)
    df_editert["Log_tid"] = pd.to_datetime(df_editert["Log_tid"])
    print("Sammenligne2")
    df_editert = df_editert.loc[df_editert["Log_tid"] <= datetime.fromtimestamp(timestamp)]
    print("Sammenligne3")
    df = pd.read_sql(f'SELECT * FROM {config["tabeller"]["raadata"]} WHERE Variabel = "{variabel}"', con=engine)
    print("Sammenligne4")
    dff = pd.concat([df, df_editert])
    dff = dff.sort_values(by="Log_tid", ascending=False)
    dff = dff.drop_duplicates(subset=["VARIABEL", "orgnrNavn"], keep="first")
    df = df.loc[df["VARIABEL"] == variabel]
    dff = dff.loc[dff["VARIABEL"] == variabel]
    df["År_2021"] = df["År_2021"].astype("float")
    dff["År_2021"] = dff["År_2021"].astype("float")
    df_r = df.groupby([aggregat, "VARIABEL"]).sum().reset_index()
    df_e = dff.groupby([aggregat, "VARIABEL"]).sum().reset_index()
    df_re = pd.merge(df_r, df_e, on = [aggregat, "VARIABEL"])
    df_re["diff"] = (df_re["År_2021_y"]-df_re["År_2021_x"])/df_re["År_2021_x"]*100
    df_re = df_re.sort_values(by=aggregat, ascending=True)
    df_re.loc[(df_re["diff"] != 0) & (df_re["diff"].notna())]
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x = df_re[aggregat], y = df_re["År_2021_x"], name = "Editerte")
    )
    fig.add_trace(
        go.Scatter(x = df_re[aggregat], y = df_re["År_2021_y"], name = "Før editering")
    )
    fig.update_layout(title = "Editerte vs rådata sammenligning etter aggregat")
    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(x = df_re[aggregat], y = df_re["diff"])
    )
    fig2.update_layout(title = "Editerte vs rådata sammenligning etter aggregat, prosentvis")
    print("Sammenligne - ferdig")
    return [dcc.Graph(figure=fig), dcc.Graph(figure=fig2)]


def main():
    print("Sett inn tester her")

if __name__ == "__main__":
    main()
print("models_grid.py lastet")