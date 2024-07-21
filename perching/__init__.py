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
        if genus[0].isupper() and not any(char.isdigit() for char in genus):
            return genus
    return None


def get_season(date):
    month = date.month
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    elif month in [9, 10, 11]:
        return "Autumn"


# Get unique values for the dropdown options
df = pd.read_csv("data/london_observations-2022.csv")
# Fill the 'perching_genus' column where it is empty and 'description' contains a genus
df["observed_on"] = pd.to_datetime(df["observed_on"], format="%d/%m/%Y")
df["season"] = df["observed_on"].apply(get_season)
df["field:perching on"] = df.apply(
    lambda row: extract_genus(row["description"])
    if pd.isnull(row["field:perching on"]) and extract_genus(row["description"])
    else row["field:perching on"],
    axis=1,
)
df = df.dropna(subset=["field:perching on"])
df["perching_genus"] = df["field:perching on"].apply(lambda x: x.split()[0])
unique_perching_on = sorted(df["perching_genus"].unique())

df_grouped = (
    df.groupby(["perching_genus", "taxon_family_name"]).size().reset_index(name="count")
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
        dcc.Graph(id="season_family_count_graph"),
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


# Prepare data for the second static line chart
# Filter perching_genus with more than 50 observations
genus_counts = df["perching_genus"].value_counts()
valid_genus = genus_counts[genus_counts > 50].index

# Filter the DataFrame to include only valid genus
filtered_df = df[df["perching_genus"].isin(valid_genus)]

# Aggregate data by season and genus
season_family_counts = (
    filtered_df.groupby(["season", "perching_genus"])["taxon_family_name"]
    .nunique()
    .reset_index()
)
season_family_counts.rename(columns={"taxon_family_name": "family_count"}, inplace=True)
print(season_family_counts)

# Ensure the seasons are in the correct order
season_order = ["Winter", "Spring", "Summer", "Autumn"]
season_family_counts["season"] = pd.Categorical(
    season_family_counts["season"], categories=season_order, ordered=True
)
season_family_counts = season_family_counts.sort_values("season")

# Create the line chart
line_fig = go.Figure()

for genus in valid_genus:
    genus_data = season_family_counts[season_family_counts["perching_genus"] == genus]
    line_fig.add_trace(
        go.Scatter(
            x=genus_data["season"],
            y=genus_data["family_count"],
            mode="lines+markers",
            name=genus,
        )
    )

line_fig.update_layout(
    title="Number of Families Observed by Season",
    xaxis_title="Season",
    yaxis_title="Number of Families",
    xaxis=dict(tickmode="array", tickvals=season_order, ticktext=season_order),
)


# Static line chart graph
@app.callback(
    Output("season_family_count_graph", "figure"),
    Input("perching_on_dropdown", "value"),
)
def update_static_line_graph(selected_perching_on):
    return line_fig


app.run_server(debug=True)
