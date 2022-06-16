## Dette repo inneholder kildekode som kan brukes som utgangspunkt for å ta i bruk metoder og visualiseringer fra Edith til egen statistikk



## Hvordan komme i gang med Edith?

1) Klon dette repo til ditt eget område får å få tak i alle filer.
Oppskrift: https://statistics-norway.atlassian.net/wiki/spaces/IA/pages/3052699649/Hvordan+pne+og+bruke+Edith+p+egne+data

   
2) Filer som må endres:
<i>Hjelp til riktig oppsett, se "Oppsett_config_og_database.ipynb"</i>
    * config.json 
        - må lages, mal for oppsett hentes ved kloning 
        - Beskrivelse av de ulike feltene ligger i Oppsett_config_og_database.ipynb
        - Endre til -dine- data, husk å endre filsti til hvor sqlite-databasen skal lagres (lages i punkt 3)
    * variabler.json
        - må lages for håndtering av variabler. Velg de viktigste numeriske variablene (eller alle)
        - Variabelnavnene pakkes inn i anførselstegn og skilles med komma. Eks:
            ...,"LOSJIOMSETNING", "OVERNATT_FRITID", "OVERNATT_FORR",...
    * app.py (hvis Edith skal kjøres som app utenfor notebook. Fungerer p.t kun på sl-inno-p1) 
       - Inneholder hardkodet brukernavn og passord. Default (TEMP - TEMP)
       - Sjekk port for kjøring (aller nederste linje i fil. Velg en port du har lagt til i putty)



3) Kjør oppretting_database_raadata.ipynb for å etablere datagrunnlag (tabell raadata) 
    * OBS! Riktig Oracle-passord kreves oppgitt i celle 5
    * Velg "Run" - "Run all cells"
    * OBS! Skal felt_id-variabelen fra DYNAREV hete noe annet? I default-oppsett er dette endret til VARIABEL (<i>FELT_ID as VARIABEL i celle 8 </i> ) . Ved endring til et annet navn kreves også endringer i templates-, og models-filer. 

4) Kjør opprett_tabell_svarinngang.ipynb for å etablere tabell for svarinngang 
   * OBS! Riktig Oracle-passord kreves oppgitt i celle 3
   * Velg "Run" - "Run all cells"
   
#### For oppstart fra notebook
5) Åpne "Edith notebook.ipynb" i JupyterLab. Følg instruksjonene.
 
    * Får du feilmeldinger i oppstart slik at Jupyterlab henger? Restart kernel

    * Feilmeldinger/debug kan skrus av og på (True/False) nederst i nest siste celle:
        app.run_server(<b>debug=True</b>, port=str(portnummer), mode=visningsmodus)

    * For å stoppe app'en, kjør nederste celle i notebook'en