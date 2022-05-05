from models.models_delt import connect, cardify_figure, table # For å importere grunnfunksjonalitet fra den delte filen
conn, engine, db = connect() # Oppretter filstier som brukes i spørringer

from dash.exceptions import PreventUpdate

import pandas as pd
import numpy as np

import plotly.graph_objects as go

import dash_core_components as dcc
import dash_html_components as html

import json

with open("config.json") as config: # Laster in valg fra config.json
    config = json.load(config)


#Funksjon som brukes i svarinngang_tbl1  
def klargjor_tbl1_svar(df, dropdown, navn):
    print("Svarinngang - tabell - klargjør tabell")
    #Grupperer på felt id, og rev kode
    tab = df.groupby(['FELT_ID', 'REV_KODE'])[['FELT_VERDI']].count()
    #pivoterer
    tab = tab.pivot_table(index="FELT_ID", columns="REV_KODE", values="FELT_VERDI")
    #Om det eksisterer U tar den summen av R og U eller er total bare R
    if 'U' in tab:
        tab['Total'] = tab['R'] + tab['U']
    else:
        tab['Total'] = tab['R']
    #Prosent    
    tab['Prosent editert'] = (tab['R']/tab['Total'])
    tab.reset_index(inplace = True)
    #Erstatter variabel med "navn" er "viktig" eller "alle"
    tab['FELT_ID'] = tab['FELT_ID'].replace([dropdown.upper()], navn)
    tab = tab.rename(columns={'FELT_ID': 'Viktighet basert på terskelverdi'})
    print("Svarinngang - tabell - klargjort tabell")
    return tab


#Callbacks

# Homepage
"""
@app.callbacks(Output('plot1', 'figure'),
               [Input('homepage_dropdown', 'value'),
                Input('homepage_input', 'value')])
"""
def svarinngang_linje(dropdown, input_svarinngang):
    print("Svarinngang - linjeplot")
    if dropdown:
        print(dropdown)
        """
        Hvis appen blir treig av å måtte laste inn data kan det eventuelt splittes opp slik at den henter inn data til en
        dcc.Store, som deretter hentes inn av hver enkelt funksjon. Det vil redusere antallet SQL spørringer en god del.
        """
        df = pd.read_sql(f"SELECT * from {config['tabeller']['svarinngang']} WHERE FELT_ID = '{dropdown.upper()}'", con=engine, parse_dates=['INN_DATO'])
        print(df.head(1))
        df = df.sort_values("INN_DATO")
        try:
            fig = go.Figure() # Lager grafobjektet for plotly
            """ Lager linje for uviktige enheter """
            df["andel"] = 1/len(df)
            df["cumulative"] = df["andel"].cumsum()
            print(df.head(1))
            fig.add_trace(go.Scatter(x = df["INN_DATO"], y = df["cumulative"], name = "Uviktig"))
            """ Lager linje for viktige enheter """
            df = df.loc[df["FELT_VERDI"] > input_svarinngang]
            df["andel"] = 1/len(df)
            df["cumulative"] = df["andel"].cumsum()
            print(df.head(1))
            fig.add_trace(go.Scatter(x = df["INN_DATO"], y = df["cumulative"], name = "Viktig"))
            
            # OBS! Det nedenfor er kun som et eksempel på hvordan man kan inkludere markering for svarfrist o.l. i figuren
            """ Enten kan man lage en dictionary med datoer man ønsker markert, eller koble det til en dataframe """
            timestamps = {
                "Svarfrist": {
                    "dato": [df["INN_DATO"].mean(), df["INN_DATO"].mean()]
                }
            }
            for i in timestamps:
                fig.add_trace(go.Scatter(x = timestamps[i]["dato"], y = [0,1], name = i)) # Bytt ut df["INN_DATO"].mean() med variabel for svarfrist så fungerer det
            # OBS! Det over er kun som et eksempel
            
            return dcc.Graph(id = "linjeplot_svarinngang", figure = fig)
        except: # Siden det er mulig å velge en verdi utenfor de som eksisterer i dataene er det lagt inn feilmelding om dette skjer.
            return html.H5(f"Du har valgt en terskelverdi som er ugyldig. Velg en verdi som er mellom 0 og {int(df.FELT_VERDI.max())} for {dropdown}.")
    else:
        return no_update
    
    """
@app.callbacks(Output('pie', 'figure'),
               [Input('homepage_dropdown', 'value'),
                Input('homepage_input', 'value')])
"""
def svarinngang_kake(dropdown, hm_input):
    print("Svarinngang - piechart")
    if dropdown:
        #Henter ut data basert på dropdown
        #dette kan forbedres. Det hentes ut samme data 3 steder, for linje, kake og tabell. Det burde heller hentes ut en gang og lagres i en store som det så burde hentes fra.
        df = pd.read_sql(f"SELECT * from svarinngang WHERE FELT_ID = '{dropdown.upper()}'", con=engine, parse_dates=['INN_DATO', 'REV_DATO']) 
        #Erstatter ved bruk av loc
        df.loc[df['REV_DATO'].isnull(),'editert'] = 'IE'
        df.loc[df['REV_DATO'].notnull(), 'editert'] = 'E'

        #df = pd.DataFrame(df)
        df['FELT_VERDI'] = df['FELT_VERDI'].fillna(0)
        if hm_input <= df.FELT_VERDI.max():
            conditions = [
                (df["FELT_ID"].eq(str(dropdown).upper()) & df["FELT_VERDI"].ge(int(hm_input)) & df["editert"].eq("E")),
                (df["FELT_ID"].eq(str(dropdown).upper()) & df["FELT_VERDI"].ge(int(hm_input)) & df["editert"].eq("IE")),
                (df["FELT_ID"].eq(str(dropdown).upper()) & df["FELT_VERDI"].lt(int(hm_input)) & df["editert"].eq("E")),
                (df["FELT_ID"].eq(str(dropdown).upper()) & df["FELT_VERDI"].lt(int(hm_input)) & df["editert"].eq("IE"))
            ]
            choices = ["Viktig editert", "Viktig ikke editert", "Uviktig editert", "Uviktig ikke editert"]

            #Gir gruppene label etter viktighet og editering

            df["gruppe_editert"] = np.select(conditions, choices)


        #figur
            labels = df['gruppe_editert'].value_counts().index
            values = df['gruppe_editert'].value_counts().values

            fig = go.Figure(data =[go.Pie(labels=labels, values = values)])
            graph = dcc.Graph(id = 'pie_plt', figure = fig)
            return graph
        
        else:
            return html.H5("")
    else:
        return no_update

        """
@app.callbacks(Output('forside-tabell', 'figure'),
               [Input('homepage_dropdown', 'value'),
                Input('homepage_input', 'value')])
"""
def svarinngang_tbl1(dropdown, hm_input):
    print("Svarinngang - tabell")
    if dropdown:
        df = pd.read_sql(f"SELECT * from svarinngang WHERE FELT_ID = '{dropdown.upper()}'", con=engine, parse_dates=['INN_DATO', 'REV_DATO'])
        df['REV_KODE'] = df['REV_KODE'].fillna('U')
        df_alle = klargjor_tbl1_svar(df, dropdown=dropdown, navn='Alle')
        print("Svarinngang - tabell - 1")
        if hm_input:
            try:
                print("Svarinngang - tabell - 2")
                df_terskel = df[df['FELT_VERDI']>int(hm_input)]
                df_viktig = klargjor_tbl1_svar(df_terskel, dropdown=dropdown, navn='Viktig')

                tab3 = pd.concat([df_alle, df_viktig])
                tab3['Prosent editert'] = tab3['Prosent editert'].astype(float).map("{:.1%}".format)
                print("Svarinngang - tabell - 3")
                if 'U' in tab3:
                    print("Svarinngang - tabell - 3a")
                    tab4 = tab3.append({'Viktighet basert på terskelverdi': "Andel viktige foretak",
                                        'R': tab3['R'].iloc[1]/tab3['R'].iloc[0],
                                        'U': tab3['U'].iloc[1]/tab3['U'].iloc[0],
                                        'Total': tab3['Total'].iloc[1]/tab3['Total'].iloc[0],
                                       'Prosent editert': 0}, ignore_index = True)
                else:
                    print("Svarinngang - tabell - 3b")
                    tab4 = tab3.append({'Viktighet basert på terskelverdi': "Andel viktige foretak",
                                        'R': tab3['R'].iloc[1]/tab3['R'].iloc[0]*100,
                                        'Total': tab3['Total'].iloc[1]/tab3['Total'].iloc[0],
                                       'Prosent editert': 0}, ignore_index = True)

                tab4.columns.name=''

                #tab4 = tab4.round(0)
                #if 'U' in tab4:
                #    tab4 = tab4.rename(columns={'R': 'Editert', 'U': 'Rådata'}).set_index('Viktighet basert på terskelverdi', drop = True)
                #else:
                #    tab4 = tab4.rename(columns={'R': 'Editert'}).set_index('Viktighet basert på terskelverdi', drop = True)
                tab4 = tab4.set_index('Viktighet basert på terskelverdi', drop = True).T
                tab4 = tab4.fillna(0)
                tab4['Andel viktige foretak'] = tab4['Andel viktige foretak'].astype(float).map("{:.1%}".format)
                tab4.loc['Prosent editert'][-1] = '-' 
                print("Svarinngang - tabell - 4")
                tab4 = tab4.reset_index()
                data = tab4.to_dict('rows')
                columns = [{'name': i, 'id': i} for i in tab4.columns]
                print("Svarinngang - tabell - 5")
                return table(id = 'forside-tabell', data = data, columns = columns, filterable=False)
            except Exception:
                print("Svarinngang - tabell - Noe gikk galt etter punkt 2")
                return html.H5("")
        else:
            return no_update
    else:
        return no_update


def main():
    print("Sett inn tester her")

if __name__ == "__main__":
    main()
print("models_homepage.py lastet")