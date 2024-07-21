import re
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# Initialize the Dash app
app = dash.Dash(__name__)


def extract_genus(description):
    if pd.isnull(description):
        return None
    match = re.search(r"\((\w+)\s+\w+\)$", description)
    if match:
        genus = match.group(1)
        if not any(char.isdigit() for char in genus):
            return genus
    return None


# Get unique values for the dropdown options
df = pd.read_csv("data/london_observations-2022.csv")
# Fill the 'perching_genus' column where it is empty and 'description' contains a genus
df["field:perching on"] = df.apply(
    lambda row: extract_genus(row["description"])
    if pd.isnull(row["field:perching on"]) and extract_genus(row["description"])
    else row["field:perching on"],
    axis=1,
)
df_filtered = df.dropna(subset=["field:perching on"])
df_filtered["perching_genus"] = df_filtered["field:perching on"].apply(
    lambda x: x.split()[0]
)
unique_perching_on = sorted(df_filtered["perching_genus"].unique())

df_grouped = (
    df_filtered.groupby(["perching_genus", "taxon_family_name"])
    .size()
    .reset_index(name="count")
)

print(df_grouped.head())

# Layout of the app
app.layout = html.Div(
    [
        dcc.Dropdown(
            id="perching_on_dropdown",
            options=[{"label": perch, "value": perch} for perch in unique_perching_on],
            value=unique_perching_on[0],  # Set a default value
        ),
        dcc.Graph(id="family_count_graph"),
    ]
)


# Callback to update the graph based on selected dropdown value
@app.callback(
    Output("family_count_graph", "figure"), Input("perching_on_dropdown", "value")
)
def update_graph(selected_perching_on):
    filtered_df = df_grouped[df_grouped["perching_genus"] == selected_perching_on]

    fig = go.Figure(
        data=[
            go.Bar(
                x=filtered_df["taxon_family_name"],
                y=filtered_df["count"],
                marker=dict(color="blue"),
            )
        ]
    )

    fig.update_layout(
        title=f"Counts of Families Perching on {selected_perching_on}",
        xaxis_title="Family",
        yaxis_title="Count",
    )

    return fig


app.run_server(debug=True)
