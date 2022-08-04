import dash
import dash_core_components as dcc
from dash import no_update
from dash.exceptions import PreventUpdate
import dash_html_components as html

import json

import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go

from models.models_delt import connect, cardify_figure, table # For å importere grunnfunksjonalitet fra den delte filen
conn, engine, db = connect() # Oppretter filstier som brukes i spørringer

with open("config.json") as config:
    config = json.load(config)

def feilliste_figurer(feilliste, enhet_rad, tabelldata):
    valgt_rad          = tabelldata[enhet_rad["row"]]
    enhet_klikket      = valgt_rad["ORGNR"]
    enhet_klikket_navn = valgt_rad["NAVN"]
    FELT_ID            = valgt_rad["FELT_ID"]
    aktuell_feilliste          = valgt_rad["feilliste"] 
    print("FELT ID er: " + FELT_ID)
    enhet_klikket_orgnrnavn = enhet_klikket + ": " + enhet_klikket_navn
    spørring = f"SELECT * FROM raadata "
    print("Eksperiment3: " + str(aktuell_feilliste))

    innhold = []

    if aktuell_feilliste in [
        ' Urealistisk pris',
        'Urealistisk pris',
        'Utgift til leasing virker feil',
        'Leieutgift til leasing av driftsbyg virker urealistisk lav',
        'Leieutgift til leasing av bygningsinventar virker urealistisk lav',
        'Investeringen virker urealistisk lav',
        ' Utgifter til vedlikehold virker urealisktisk høy',
        'Investering i driftsbyg virker urealisktisk høy',
        ' Utgift til leasing virker feil',
        'Investering i inventar virker urealisktisk høy',
        'Utgifter til vedlikehold virker urealisktisk lav',
        'Utgifter til vedlikehold virker urealisktisk høy',
        'Urealistisk høy kjøpesum'
    ]:
        spørring = spørring + f"WHERE VARIABEL in ('{FELT_ID}')"
        df = pd.read_sql(spørring, con = engine)
        df["År_2021"] = df["År_2021"].astype(int)
        df = df.loc[df["År_2021"] > 1]
        fig = go.Figure()

        dff = df.loc[df["ORGNR"] != enhet_klikket]
        dff = dff.groupby("Driftsform").quantile(0.1).reset_index()
        fig.add_trace(go.Bar(x = dff["Driftsform"], y = dff["År_2021"], name = "Bunn 10%", text = dff["År_2021"].round(), marker_color = "blue"))

        dff = df.loc[df["ORGNR"] != enhet_klikket]
        dff = dff.groupby("Driftsform").mean().reset_index()
        fig.add_trace(go.Bar(x = dff["Driftsform"], y = dff["År_2021"], name = "Snitt", text = dff["År_2021"].round(), marker_color = "green"))

        dff = df.loc[df["ORGNR"] != enhet_klikket]
        dff = dff.groupby("Driftsform").quantile(0.9).reset_index()
        fig.add_trace(go.Bar(x = dff["Driftsform"], y = dff["År_2021"], name = "Topp 10%", text = dff["År_2021"].round(), marker_color = "red"))

        dff = df.loc[df["ORGNR"] == enhet_klikket]
        dff = dff.groupby("Driftsform").mean().reset_index()
        fig.add_trace(go.Bar(x = dff["Driftsform"], y = dff["År_2021"], name = enhet_klikket, text = dff["År_2021"].round(), marker_color = "brown"))

        innhold = innhold + [dcc.Graph(figure = fig)]

    if aktuell_feilliste in ["Forbruk av el er lavt"]:
        spørring = spørring + "WHERE VARIABEL in ('ELFORBRUK', 'ELUTGIFTER')"
        df = pd.read_sql(spørring, con = engine)

        df = df.loc[df["VARIABEL"].isin([f'ELFORBRUK', f'ELUTGIFTER'])]
        df = df.pivot(index='ORGNR', columns='VARIABEL', values='År_2021').reset_index()
        df = df.dropna(subset = [f'ELFORBRUK', f'ELUTGIFTER'])
        df[f"ELFORBRUK"] = df[f"ELFORBRUK"].astype(int)
        df[f"ELUTGIFTER"] = df[f"ELUTGIFTER"].astype(int)

        df.loc[df["ORGNR"] == enhet_klikket, "valgt"] = enhet_klikket
        df.loc[df["ORGNR"] != enhet_klikket, "valgt"] = "Andre"
        fig = px.scatter(df, x = "ELFORBRUK", y = "ELUTGIFTER", color = "valgt")
        innhold = innhold + [dcc.Graph(figure = fig)]

    if aktuell_feilliste in ["Pris pr liter diesel (drivstoff) bør ligge mellom 5 og 25 kr"]:
        spørring = spørring + "WHERE VARIABEL in ('DIESELDRIVFORBRUK', 'DIESELDRIVUTGIFTER')"
        df = pd.read_sql(spørring, con = engine)
        df = df.sort_values(by = "LOPENR")
        df = df.drop_duplicates(subset = ["ENHETS_ID", "ORGNR", "VARIABEL"])
        df = df.loc[df["VARIABEL"].isin([f'DIESELDRIVFORBRUK', f'DIESELDRIVUTGIFTER'])]
        df = df.pivot(index='ORGNR', columns='VARIABEL', values='År_2021').reset_index()
        df = df.dropna(subset = [f'DIESELDRIVFORBRUK', f'DIESELDRIVUTGIFTER'])
        df[f"DIESELDRIVFORBRUK"] = df[f"DIESELDRIVFORBRUK"].astype(int)
        df[f"DIESELDRIVUTGIFTER"] = df[f"DIESELDRIVUTGIFTER"].astype(int)

        df.loc[df["ORGNR"] == enhet_klikket, "valgt"] = enhet_klikket
        df.loc[df["ORGNR"] != enhet_klikket, "valgt"] = "Andre"
        fig = px.scatter(df, x = "DIESELDRIVFORBRUK", y = "DIESELDRIVUTGIFTER", color = "valgt")
        innhold = innhold + [dcc.Graph(figure = fig)]

    if aktuell_feilliste in [
        "Pris pr SM3 propan bør ligge mellom 2000 og 12000 kroner",
        "Pris pr tonn propan bør ligge mellom 1000 og 20000 kroner",
        "Pris pr KWH propan bør ligge mellom 0,5 og 7 kroner",
        "Pris pr tonn halm bør ligge mellom 100 og 1000 kroner",
        " Pris pr M3 flis bør ligge mellom 10 og 500 kroner",
        "Pris pr M3 flis bør ligge mellom 10 og 500 kroner"
    ]:
        print("Finner vare")
        vare = FELT_ID[:-8]
        print(vare + " er valgt vare")
        spørring = spørring + f"WHERE VARIABEL in ('{vare}ENHET', '{vare}FORBRUK', '{vare}UTGIFTER')"
        df = pd.read_sql(spørring, con = engine)
        df = df.drop_duplicates()
        df = df.pivot(
            index='ORGNR',
            columns='VARIABEL',
            values=config["perioder"]["t"]["periode"]
        ).reset_index()
        df = df.dropna(subset = [f'{vare}ENHET', f'{vare}FORBRUK', f'{vare}UTGIFTER'])
        df[f"{vare}FORBRUK"] = df[f"{vare}FORBRUK"].str.replace(",",".")
        df[f"{vare}UTGIFTER"] = df[f"{vare}UTGIFTER"].str.replace(",",".")
        df[f"{vare}FORBRUK"] = df[f"{vare}FORBRUK"].astype(float)
        df[f"{vare}UTGIFTER"] = df[f"{vare}UTGIFTER"].astype(float)
#        dff = df.loc[dff[f"{vare}ENHET"] == i]
        df.loc[df["ORGNR"] == enhet_klikket, "valgt"] = enhet_klikket
        df.loc[df["ORGNR"] != enhet_klikket, "valgt"] = "Andre"
        fig = px.scatter(df, x = f"{vare}FORBRUK", y = f"{vare}UTGIFTER", hover_name = df.index, trendline = "ols", color = "valgt")
        innhold = innhold + [dcc.Graph(figure = fig)]

    return innhold