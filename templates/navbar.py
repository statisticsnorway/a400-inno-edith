import dash_bootstrap_components as dbc


def Navbar():
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Grid", href="/grid")),
            dbc.NavItem(dbc.NavLink("Enhet", href="/enhet")),
            dbc.NavItem(dbc.NavLink("Logg", href="/logg")),
            dbc.NavItem(dbc.NavLink("Kontrollér", href="/kontroller"))
        ],
        brand = "Svarinngang",
        brand_href="/svarinngang",
        sticky="top",
        id = "Navbar" # La til en ID
    )
    return navbar

