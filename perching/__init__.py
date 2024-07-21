import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

app = Dash(__name__)


df = pd.read_csv("data/victor_observations.csv")
print(df.head())

app.layout = html.Div(
    [
        html.H4("Interactive color selection with simple Dash example"),
        html.P("Select color:"),
        dcc.Dropdown(
            id="dropdown",
            options=["Gold", "MediumTurquoise", "LightGreen"],
            value="Gold",
            clearable=False,
        ),
        dcc.Graph(id="graph"),
    ]
)


@app.callback(Output("graph", "figure"), Input("dropdown", "value"))
def display_color(color):
    fig = go.Figure(
        data=go.Bar(
            y=[2, 3, 1], marker_color=color  # replace with your own data source
        )
    )
    return fig


app.run_server(debug=True)
