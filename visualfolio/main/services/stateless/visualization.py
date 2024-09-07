import colorsys
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import textwrap
import requests
import pandas as pd
import datetime
import plotly.graph_objects as go
from plotly.offline import plot
import numpy as np


from main.services.stateless.plotly_config import (
    plotly_layout,
    plotly_configuration,
    opacity,
)


def hex_to_hsl_components(hex_color):
    hex_color = hex_color.lstrip("#")

    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0

    h, l, s = colorsys.rgb_to_hls(r, g, b)

    return int(h * 360), int(s * 100), int(l * 100)


def humanize_number(value, fraction_point=1):
    """
    Converts float values to strings such as "10K", "200M" etc.
    """

    powers = [10**x for x in (12, 9, 6, 3, 0)]
    human_powers = ("T", "B", "M", "K", "")

    if not isinstance(value, float):
        value = float(value)

    for i, p in enumerate(powers):
        if value >= p:
            return_value = (
                str(
                    int(
                        round(value / (p / (10.0**fraction_point)))
                        / (10**fraction_point)
                    )
                )
                + human_powers[i]
            )
            break

    return return_value


def generate_streamgraph(df, theme, base_currency, color_map, last_group_name):
    # Convert dates to datetime format
    df["date"] = pd.to_datetime(df["date"])

    main_color = {"light": "#6b6b6b", "dark": "#acacac"}

    # Calculate y-axis range
    y_range = (
        df["rel_value_transactions_only"].max()
        - df["inverted_rel_value_capital_gain_only"].min()
    )
    y_min = df["inverted_rel_value_capital_gain_only"].min() - (y_range * 0.25)
    y_max = df["rel_value_transactions_only"].max() + (y_range * 0.15)

    # Initialize streamgrapgh
    fig = go.Figure()

    # Upper boundary
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["rel_value_transactions_only"],
            mode="lines",
            line_shape="hv",
            line=dict(color=main_color[theme], width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Internal boundaries
    internal_boundaries = [c for c in df.columns if c.endswith("_internal_boundary")]
    for i, col in enumerate(internal_boundaries):
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[col],
                mode="lines",
                hoverinfo="skip",
                fill="tonexty",
                fillcolor=color_map.at[col.split("_")[0], f"hsl_{theme}_background"]
                .replace("hsl(", "hsla(")
                .replace(")", f",{opacity[theme]})"),
                line=dict(color=main_color[theme], width=1),
                name=col.split("_")[0],
            )
        )

    # Lower boundary
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["inverted_rel_value_capital_gain_only"],
            mode="lines",
            hoverinfo="skip",
            fill="tonexty",
            fillcolor=color_map.at[
                internal_boundaries[-1].split("_")[1], f"hsl_{theme}_background"
            ]
            .replace("hsl(", "hsla(")
            .replace(")", f",{opacity[theme]})"),
            line=dict(color=main_color[theme], width=1),
            name=last_group_name,
        )
    )

    # Adjusted mock trace for hover data (invisible)
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=[(y_min + y_max) / 2] * len(df),
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),  # Invisible
            showlegend=False,
            customdata=df["value"],
            hovertemplate="Total asset value: %{customdata:,.2f} " + base_currency,
            hoverlabel=dict(namelength=0),
        )
    )

    # Add ruler

    # Hard-code horizontal axis in order to add a ruler that is aligned to an axis gap
    intervals = [x * 10**i for i in range(0, 10) for x in (1, 2, 5)]

    diff = (y_max - y_min) / 10
    chosen_interval = min(intervals, key=lambda x: abs(x - diff))
    num_lines = int((y_max - y_min) // chosen_interval)
    if num_lines % 2 == 1:
        num_lines += 1

    y_axis_lines = [y_min + i * chosen_interval for i in range(num_lines + 1)]
    y_range = [
        y_min,
        y_min + chosen_interval * num_lines * 1.01,
    ]  # Increment slightly so that the top line renders

    # Calculate ruler x
    timespan = df["date"].max() - df["date"].min()
    ruler_x = df["date"].min() + 0.05 * timespan
    annotation_x = df["date"].min() + 0.02 * timespan

    # Add ruler line
    fig.add_shape(
        type="line",
        x0=ruler_x,
        x1=ruler_x,
        y0=y_axis_lines[-2],
        y1=y_axis_lines[-3],
        line=dict(color=main_color[theme], width=2),
    )

    # Add top dash of the "I"
    fig.add_shape(
        type="line",
        x0=ruler_x - 0.001 * timespan,
        x1=ruler_x + 0.005 * timespan,
        y0=y_axis_lines[-2],
        y1=y_axis_lines[-2],
        line=dict(color=main_color[theme], width=2),
    )

    # Add bottom dash of the "I"
    fig.add_shape(
        type="line",
        x0=ruler_x - 0.001 * timespan,
        x1=ruler_x + 0.005 * timespan,
        y0=y_axis_lines[-3],
        y1=y_axis_lines[-3],
        line=dict(color=main_color[theme], width=2),
    )

    # Add text annotation for the line length
    line_length = y_axis_lines[2] - y_axis_lines[1]
    fig.add_annotation(
        x=annotation_x,
        y=(y_axis_lines[-2] + y_axis_lines[-3]) / 2,
        text=f"{base_currency} {humanize_number(line_length)}",
        showarrow=False,
        font=dict(size=12, color=main_color[theme]),
        align="right",
    )

    fig.update_layout(plotly_layout[theme])

    fig.update_layout(
        height=500,
        hovermode="x",
        margin=dict(l=20, r=20, t=20, b=30),
        xaxis=dict(
            zeroline=False,
            zerolinewidth=1,
            showgrid=False,
            showspikes=True,
            spikemode="across",
            spikethickness=1,
            spikedash="dash",
            spikecolor="gray",
        ),
        yaxis=dict(
            range=y_range,
            tickvals=y_axis_lines,
            zeroline=False,
            zerolinewidth=1,
            showgrid=True,
            showticklabels=False,
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0),
        legend_itemclick=False,  # Disable single-click interactivity
        legend_itemdoubleclick=False,  # Disable double-click interactivity
    )

    graph_div = plot(
        fig,
        output_type="div",
        config={**plotly_configuration, "scrollZoom": False, "displayModeBar": False},
    )

    return graph_div
