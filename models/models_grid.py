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
        print("----- Starter treemap grid -----")
        print()
        if len(var) == 1:
            df = pd.read_sql(f'SELECT * FROM {config["tabeller"]["raadata"]} WHERE VARIABEL in ("{var[0]}")', con=engine)
            try: # Slår sammen editeringer med rådata
                df_e = pd.read_sql(f'SELECT * FROM {config["tabeller"]["editeringer"]} WHERE VARIABEL in ("{var[0]}")', con=engine)
                editeringer = True
            except:
                editeringer = False
                print("Ingen endringer er loggført")
            if editeringer != False:
                df = pd.concat([df, df_e], ignore_index = True)
                df = df.sort_values(by="Log_tid", ascending=False)
                df = df.drop_duplicates(subset=["VARIABEL", "orgnrNavn"], keep="first")
        if len(var) > 1:
            df = pd.read_sql(f"SELECT * FROM {config['tabeller']['raadata']} WHERE VARIABEL in {tuple(var)}", con=engine)
            try: # Slår sammen editeringer med rådata
                df_e = pd.read_sql(f'SELECT * FROM {config["tabeller"]["editeringer"]} WHERE VARIABEL in ("{var[0]}")', con=engine)
                editeringer = True
            except:
                editeringer = False
                print("Ingen endringer er loggført")
            if editeringer != False:
                df = pd.concat([df, df_e], ignore_index = True)
                df = df.sort_values(by="Log_tid", ascending=False)
                df = df.drop_duplicates(subset=["VARIABEL", "orgnrNavn"], keep="first")

        fig = px.treemap(df.fillna("MANGLER"), path = grupp , values = config["perioder"]["t"]["periode"])
        graph = dcc.Graph(id = 'treemap', figure = fig)
        data = df.to_dict('rows')
        print("----- Avslutter treemap grid -----")
        print()
        return graph, data
    else:
        return no_update


# Dette er ikke en callback, men brukes i callbacks som styres av clickdata fra treemap
def treemap_clickdata_sjekk(grupp, clickData):
    print("treemap_clickdata_sjekk starter")
    print("Clickdata er:")
    print()
    print(str(clickData))
    print()
    nivå = None
    aggregater = None
    if clickData == None: # Er det ingen clickdata er man på øverste nivå, fordi man ikke har drillet nedover.
        nivå = "topp"
    else: # Eksisterer clickData så sjekkes innholdet mer
        if "points" in clickData:
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
    print("Nivå er: " + str(nivå))
    print()
    print("Aggregater er: " + str(aggregater))
    print()
    print("treemap_clickdata_sjekk ferdig")
    print()
    return nivå, aggregater


def table_grid(data, grupp, clickData):
    print("----- Starter tabell grid -----")
    print()
    df = pd.DataFrame(data)
    """ Forbereder lister over kolonner som skal være med videre, etter hvorvidt de er string/objekter eller numeriske kolonner """
    perioder = {}
    for i in config["perioder"]: # Finnes sikkert en bedre løsning enn dette
        perioder[i] = config["perioder"][i]["periode"] # Må kanskje finne en litt annen måte å gjøre det på hvis kobling av perioder skal skje i funksjonen
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
            a = config["perioder"][list(config["perioder"].keys())[i]]["periode"]
            num_cols.append(a)
            try:
                b = config["perioder"][list(config["perioder"].keys())[i+1]]["periode"]
                #c = config["perioder"][list(config["perioder"].keys())[i]]["år_til_år"]
                c = str(b) + " til " + str(a)
                df[c] = df[a] - df[b]
                num_cols.append(c)
            except:
                print("Ferdig med beregning av diff")
    else:
        print("Ingen beregning av diff")

    """ clickData håndtering """
    """ Finner ut hvilket nivå clickdata fra treemap peker til """
    nivå, aggregater = treemap_clickdata_sjekk(grupp, clickData)

    """ Lager riktig data til tabellen """
    if nivå != "topp":
        if aggregater is not None:
            for i in range(len(aggregater)): # Looper gjennom en filtrering 1 gang per nivå
                if aggregater[i] != None:
                    df = df.loc[df[grupp[i]] == aggregater[i]]
    df = df[grupp + str_cols + num_cols]
    if nivå != "enhet": # Så lenge det ikke er på enhetsnivå så skal det aggregeres
        df = df.groupby(grupp+["VARIABEL"]).agg({i : "sum" for i in num_cols}).reset_index()
    """ Gjør data fra dataframe klart til dash table """
    data = df.to_dict("rows")
    columns = [{'name': i, 'id': i} for i in df.columns]
    print("----- Avslutter tabell grid -----")
    print()
    return table(id = "tabell_grid", data = data, columns = columns)



def scatterplot_grid(x, y, checklist, aggregat, clickData, scatter_aggregat):
    print("----- Starter scatterplot grid -----")
    print()
    print(checklist)
    if checklist:
        if "ols" in checklist:
            trendline = "ols"
        else:
            trendline = None
        if "fjern" not in checklist:
            inkluder_0 = True
        else:
            inkluder_0 = False
    else:
        trendline = None
        inkluder_0 = False
        
    tilpasning_til_spørring = ""
    variabel_filter = f"WHERE VARIABEL in {tuple([x]+[y])} "
    tilpasning_til_spørring = tilpasning_til_spørring + variabel_filter
    
    # Finner ut hvilket nivå clickdata fra treemap peker til 
    nivå, aggregater = treemap_clickdata_sjekk(aggregat, clickData)

    # Bruker klikkdata for å lage SQL spørring
    if aggregater is not None:
        aggregering_filter = "" # Skal bruke denne for å lage en SQL spørring som en string for å filtrere datasettet
        for i in range(len(aggregater)): # Splitter clickdata sin id basert på / 
            aggregering_filter = aggregering_filter \
            + "AND " \
            + str(aggregat[i]) \
            + " = '" \
            + str(clickData["points"][0]["id"].split("/")[i]) \
            + "' " # \ på slutten er bare for å markere linjeskifte, gjør koden som lager stringen bittelitt mer leselig
        tilpasning_til_spørring = tilpasning_til_spørring + aggregering_filter
    print("Tilpasning til spørring:")
    print(tilpasning_til_spørring)
    print()
    spørring = f"SELECT * FROM {config['tabeller']['raadata']} " + tilpasning_til_spørring

    df = pd.read_sql(spørring, con = engine)
    spørring_e = f"SELECT * FROM {config['tabeller']['editeringer']} " + tilpasning_til_spørring
    try: # Slår sammen editeringer med rådata
        df_e = pd.read_sql(spørring_e, con = engine)
        editeringer = True
    except:
        editeringer = False
        print("Ingen endringer er loggført")
    if editeringer != False:
        df = pd.concat([df, df_e], ignore_index = True)
        df = df.sort_values(by="Log_tid", ascending=False)
    df = df.loc[(df["VARIABEL"].isin([x, y]))].drop_duplicates(subset=["VARIABEL", "orgnrNavn"], keep="first")
    print(f"Scatter aggregat er: {scatter_aggregat}")
    if scatter_aggregat:
        df = df.pivot(index = ["orgnrNavn", scatter_aggregat], columns=["VARIABEL"], values = config["perioder"]["t"]["periode"]).reset_index()
    else:
        df = df.pivot(index = "orgnrNavn", columns=["VARIABEL"], values = config["perioder"]["t"]["periode"]).reset_index()
    df[[x, y]] = df[[x, y]].astype(float)
    if inkluder_0 == False: # Checklist starter som None
        df = df.loc[df[x] > 0]
        df = df.loc[df[y] > 0]
    if scatter_aggregat:
        fig = px.scatter(df,x = x,y = y, hover_name = df["orgnrNavn"], trendline=trendline, color = scatter_aggregat)
    else:
        fig = px.scatter(df,x = x,y = y, hover_name = df["orgnrNavn"], trendline=trendline)
    tittel = f"Forholdet mellom {x} og {y}"
    if aggregater:
        tittel = tittel + f" blant {aggregater}"
    fig.update_layout(
        title = tittel
    )
    print("----- Avslutter scatterplot grid -----")
    print()
    return dcc.Graph(id = "scatter_grid",figure=fig)



def histogram_grid(variabel, bins, checklist, aggregat, clickData):
    print("----- Starter histogram grid -----")
    print()
    tilpasning_til_spørring = ""
    variabel_filter = f"WHERE VARIABEL = '{variabel}' "
    tilpasning_til_spørring = tilpasning_til_spørring + variabel_filter

# Finner ut hvilket nivå clickdata fra treemap peker til 
    nivå, aggregater = treemap_clickdata_sjekk(aggregat, clickData)

    # Bruker klikkdata for å lage SQL spørring
    if aggregater is not None:
        aggregering_filter = "" # Skal bruke denne for å lage en SQL spørring som en string for å filtrere datasettet
        for i in range(len(aggregater)): # Splitter clickdata sin id basert på / 
            aggregering_filter = aggregering_filter \
            + "AND " \
            + str(aggregat[i]) \
            + " = '" \
            + str(clickData["points"][0]["id"].split("/")[i]) \
            + "' " # \ på slutten er bare for å markere linjeskifte, gjør koden som lager stringen bittelitt mer leselig
        tilpasning_til_spørring = tilpasning_til_spørring + aggregering_filter
    print("Tilpasning til spørring:")
    print(tilpasning_til_spørring)
    print()
    spørring = f"SELECT * FROM {config['tabeller']['raadata']} " + tilpasning_til_spørring
    df = pd.read_sql(spørring, con = engine)
    spørring_e = f"SELECT * FROM {config['tabeller']['editeringer']} " + tilpasning_til_spørring
    try: # Slår sammen editeringer med rådata
        df_e = pd.read_sql(spørring_e, con = engine)
        editeringer = True
    except:
        editeringer = False
    if editeringer != False:
        df = pd.concat([df, df_e], ignore_index = True)
        df = df.sort_values(by="Log_tid", ascending=False)  
    df = df.drop_duplicates(subset=["VARIABEL", "orgnrNavn"], keep="first")

    # I tilfelle perioden ligger som feil datatype
    df[config["perioder"]["t"]["periode"]] = df[config["perioder"]["t"]["periode"]].astype(float)

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x = df[config["perioder"]["t"]["periode"]],
        histfunc = "count",
        histnorm = '',
        nbinsx = bins,
        name = config["perioder"]["t"]["periode"]
    ))
    tittel = f"Fordeling av enheter på {variabel}"
    if aggregater:
        tittel = tittel + f" innenfor {aggregater}"
    fig.update_layout(
        title = tittel,
        xaxis_title = f"Verdi på {variabel}",
        yaxis_title = "Antall enheter med verdien",
        barmode = "group"
    )
    print("----- Avslutter histogram grid -----")
    print()
    return dcc.Graph(id = "histogram_grid", figure = fig)



def boxplot_grid(variabel, checklist, aggregat, clickData): # Tatt ut av listen: boxpoints, 
    print("----- Starter boxplot grid -----")
    print()
    tilpasning_til_spørring = ""
    variabel_filter = f"WHERE VARIABEL = '{variabel}' "
    tilpasning_til_spørring = tilpasning_til_spørring + variabel_filter

    # Finner ut hvilket nivå clickdata fra treemap peker til 
    nivå, aggregater = treemap_clickdata_sjekk(aggregat, clickData)

    # Bruker klikkdata for å lage SQL spørring
    if aggregater is not None:
        aggregering_filter = "" # Skal bruke denne for å lage en SQL spørring som en string for å filtrere datasettet
        for i in range(len(aggregater)): # Splitter clickdata sin id basert på / 
            aggregering_filter = aggregering_filter \
            + "AND " \
            + str(aggregat[i]) \
            + " = '" \
            + str(clickData["points"][0]["id"].split("/")[i]) \
            + "' " # \ på slutten er bare for å markere linjeskifte, gjør koden som lager stringen bittelitt mer leselig
        tilpasning_til_spørring = tilpasning_til_spørring + aggregering_filter
    print("Tilpasning til spørring:")
    print(tilpasning_til_spørring)
    print()
    spørring = f"SELECT * FROM {config['tabeller']['raadata']} " + tilpasning_til_spørring
    df = pd.read_sql(spørring, con = engine)
    spørring_e = f"SELECT * FROM {config['tabeller']['editeringer']} " + tilpasning_til_spørring
    try: # Slår sammen editeringer med rådata
        df_e = pd.read_sql(spørring_e, con = engine)
        editeringer = True
    except:
        editeringer = False
    if editeringer != False:
        df = pd.concat([df, df_e], ignore_index = True)
        df = df.sort_values(by="Log_tid", ascending=False)
    df = df.drop_duplicates(subset=["VARIABEL", "orgnrNavn"], keep="first")
    for i in config["perioder"]:
        df[config["perioder"][i]["periode"]] = df[config["perioder"][i]["periode"]].astype(float)
    if checklist != None: # Checklist starter som None
        if len(checklist) != 0: # Hvis man har krysset av er lengde mer enn 0
            df = df.loc[df[config["perioder"]["t"]["periode"]] > 0]
    fig = go.Figure()
    print("Lager figur for boxplot grid")
    for i in config["perioder"]:# Lager ett trace per årgang
        fig.add_trace(go.Box(
            y=df[config["perioder"][i]["periode"]],
            name=str(config["perioder"][i]["periode"]),
            text = df['orgnrNavn']
        ))
    fig.update_traces(boxpoints = "all")
    tittel = f"Boxplot for verdier i {variabel}"
    if aggregater:
        tittel = tittel + f" innenfor {aggregater}"
    fig.update_layout(
        title = tittel,
        xaxis_title = "Periode",
        yaxis_title = variabel
    )
    print("----- Avslutter boxplot grid -----")
    print()
    return dcc.Graph(id = "boxplot_grid", figure = fig)


def sammenlign_editert_ueditert(timestamp):
    print("----- Starter sammenligning av rådata og editerte grid -----")
    print()
    aggregat = "ORG_FORM"
    variabel = "INTFOU"
    df_editert = pd.read_sql(f'SELECT * FROM {config["tabeller"]["editeringer"]}', con=engine)
    df_editert["Log_tid"] = pd.to_datetime(df_editert["Log_tid"])
    df_editert = df_editert.loc[df_editert["Log_tid"] <= datetime.fromtimestamp(timestamp)]
    df = pd.read_sql(f'SELECT * FROM {config["tabeller"]["raadata"]} WHERE Variabel = "{variabel}"', con=engine)
    dff = pd.concat([df, df_editert])
    dff = dff.sort_values(by="Log_tid", ascending=False)
    dff = dff.drop_duplicates(subset=["VARIABEL", "orgnrNavn"], keep="first")
    df = df.loc[df["VARIABEL"] == variabel]
    dff = dff.loc[dff["VARIABEL"] == variabel]
    df[config["perioder"]["t"]["periode"]] = df[config["perioder"]["t"]["periode"]].astype("float")
    dff[config["perioder"]["t"]["periode"]] = dff[config["perioder"]["t"]["periode"]].astype("float")
    df_r = df.groupby([aggregat, "VARIABEL"]).sum().reset_index()
    df_e = dff.groupby([aggregat, "VARIABEL"]).sum().reset_index()
    df_re = pd.merge(df_r, df_e, on = [aggregat, "VARIABEL"])
    df_re["diff"] = (df_re[f'{config["perioder"]["t"]["periode"]}_y']-df_re[f'{config["perioder"]["t"]["periode"]}_x'])/df_re[f'{config["perioder"]["t"]["periode"]}_x']*100
    df_re = df_re.sort_values(by=aggregat, ascending=True)
    df_re.loc[(df_re["diff"] != 0) & (df_re["diff"].notna())]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x = df_re[aggregat], y = df_re[f'{config["perioder"]["t"]["periode"]}_x'], name = "Editerte")
    )
    fig.add_trace(
        go.Scatter(x = df_re[aggregat], y = df_re[f'{config["perioder"]["t"]["periode"]}_y'], name = "Før editering")
    )
    fig.update_layout(title = "Editerte vs rådata sammenligning etter aggregat")
    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(x = df_re[aggregat], y = df_re["diff"])
    )
    fig2.update_layout(title = "Editerte vs rådata sammenligning etter aggregat, prosentvis")
    print("----- Avslutter sammenligning av rådata og editerte grid -----")
    print()
    return [dcc.Graph(figure=fig), dcc.Graph(figure=fig2)]


def main():
    print("Sett inn tester her")

if __name__ == "__main__":
    main()
print("models_grid.py lastet")