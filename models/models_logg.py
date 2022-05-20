from models.models_delt import connect, cardify_figure, table # For å importere grunnfunksjonalitet fra den delte filen
conn, engine, db = connect() # Oppretter filstier som brukes i spørringer

import pandas as pd
import dash_table as dt

import json

with open("config.json") as config:
    config = json.load(config)

def logg_tabell(url):
    print('Henter loggføringstabell')
    df = pd.read_sql(f"select * from {config['tabeller']['editeringer']}", con=engine)
    df = df[ # Kolonner som listes opp her vil vises i loggføringstabellen
        ["orgnrNavn", "VARIABEL"]
        + [config["perioder"]["t"]["år"]]
        + ["Tidligere_verdi", "Kommentar", "Editert_av", "Log_tid"]
    ]
    df = df.rename(columns = { # Hjelper på lesbarhet av tabellen, den brukes ikke til noe per dags dato så har ingen ringvirkninger
        config["perioder"]["t"]["år"]: "Ny verdi",
        "Tidligere_verdi": "Opprinnelig verdi" # Kan kanskje endre Tidligere_verdi i oppdater_database(), men egentlig ikke nødvendig
    })
    df = df.sort_values(by = "Log_tid", ascending = False)
    data = df.to_dict('records')
    columns = [{'name': i, 'id': i} for i in df.columns]
    print("Laster loggføringstabell til dashbordet")
    return dt.DataTable(
            style_cell = {'textAlign': 'left'},
            style_data = {
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            sort_action='native',
            data = data,
            columns = columns,
            filter_action='native',
            page_action = 'native',
            page_size = 100,
            sort_mode = 'multi')

def main():
    print("Sett inn tester her")

if __name__ == "__main__":
    main()
print("models_logg.py lastet")