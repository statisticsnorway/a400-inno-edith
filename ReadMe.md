## Dette repo inneholder kildekode som kan brukes som utgangspunkt for å ta i bruk metoder og visualiseringer fra Edith til egen statistikk



## Hvordan komme i gang med Edith?

1) Klon dette repo til ditt eget område får å få tak i alle filer.
Oppskrift: xxx

2) Filer som må endres:
    * config.json (beskrivelse av fil: xxx)
        - Beskrivelse av de ulike feltene ligger i Oppsett_config_og_database.ipynb
        - Endre til -dine- data, husk å endre filsti til hvor sqlite-databasen skal lagres (lages i punkt 3)
    * app.py  
       - Inneholder hardkodet brukernavn og passord. Default (TEMP - TEMP)
       - Sjekk port for kjøring (aller nederste linje i fil. Velg en port du har lagt til i putty)

3) Kjør oppretting_database_raadata.ipynb for å etablere datagrunnlag (tabell raadata) 
    - OBS! Endre til riktig Oracle-brukernavn i celle 5
    - Velg "Cell" - "Run all"
    - OBS! Skal felt_id-variabelen fra DYNAREV hete noe annet? I default-oppsett er dette endret til VARIABEL (<i>FELT_ID as VARIABEL i celle 8 </i> ) . Ved endring til et annet navn kreves også endringer i templates-, og models-filer. 

4) Kjør opprett_tabell_svarinngang.ipynb for å etablere tabell for svarinngang 
   - OBS! Endre til riktig Oracle-brukernavn i celle 3
   - Velg "Cell" - "Run all"
   
   

5) Start edith med kommandoen " python3 app.py" i et terminalvindu


* Fungerer ikke app'en helt som du har tenkt? Sjekk i terminal-vinduet! Feilmeldinger dukker opp der

* Ønsker du å stoppe kjøring av appen? I terminalen, trykk Ctrl+C