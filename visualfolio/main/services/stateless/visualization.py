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


def generate_shades(base_color, n, theme):
    """
    Generates n shades of the same hue (hue of base_color).
    """
    base_rgb = mcolors.hex2color(base_color)
    base_hue, _, _ = colorsys.rgb_to_hsv(*base_rgb)

    # Determine brightness range based on theme
    if theme == "light":
        min_brightness = 0.60
        max_brightness = 0.75

    elif theme == "dark":
        min_brightness = 0.3
        max_brightness = 0.45

    else:
        raise ValueError("Theme must be either 'light' or 'dark'.")

    # Generate shades of ascending brightness
    brightness_range = np.linspace(min_brightness, max_brightness, n)

    shades = []
    for brightness in brightness_range:
        if theme == "dark":
            # For darker ranges, since the lighter shades will appear most saturated,
            # increase saturation for brighter shades
            saturation = 1 - brightness + min_brightness -0.15  # Arbitrary correction
        else:
            # For lighter ranges, since the darker shades will appear most saturated,
            # increase saturation for brighter shades
            saturation = brightness + (1 - max_brightness)

        shade = mcolors.rgb2hex(colorsys.hls_to_rgb(base_hue, brightness, saturation))
        shades.append(shade)

    return shades


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
            line=dict(width=0),
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
                line=dict(width=0),
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
            line=dict(width=0),
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


def generate_relative_streamgraph(df, asset_class_sums, theme):
    asset_class_sums.set_index("asset_class", inplace=True)
    df.set_index("date", inplace=True)

    # Normalize data to achieve relative stream
    df_normalized = df.div(df.sum(axis=1), axis=0) * 100

    # Generate figure
    fig = go.Figure()

    # For each asset
    for col in df_normalized.columns:

        # Set fill color, adjust opacity based on theme
        fill_color = asset_class_sums.at[col, f"hsl_{theme}_background"]
        fill_color = fill_color.replace("hsl(", "hsla(").replace(
            ")", f",{opacity[theme]})"
        )

        fig.add_trace(
            go.Scatter(
                x=df_normalized.index,
                y=df_normalized[col],
                mode="lines",
                stackgroup="one",
                line=dict(width=0),
                fillcolor=fill_color,
                name=col,
                hoverinfo="x+y+name",
                hoveron="points+fills",
                fill="tonexty",
                hovertemplate="%{y:.2f}%" + f"<extra><b style='color:{fill_color};'>" + col + "</b></extra>",
                cliponaxis=False,
            )
        )

    # Add legend
    fig.update_layout(
        yaxis=dict(tickmode="array", tickvals=[20, 40, 60, 80]),
        showlegend=True,
    )

    # Set style
    fig.update_layout(plotly_layout[theme])
    fig.update_layout(
        height=196,
        autosize=True,
        hovermode="x",
        margin=dict(l=25, r=25, t=15, b=35),
        xaxis=dict(
            zeroline=False,
            zerolinewidth=1,
            showgrid=False,
            showspikes=True,
            spikemode="across",
            spikethickness=1,
            spikedash="dash",
            spikecolor="gray",
            spikesnap="cursor",
        ),
        showlegend=False,
        yaxis=dict(
            zeroline=False,
            zerolinewidth=1,
            showgrid=True,
            showticklabels=False,
        ),
    )

    graph_div = plot(
        fig,
        output_type="div",
        config={**plotly_configuration, "scrollZoom": False, "displayModeBar": False},
    )

    return graph_div


def generate_assets_donut(assets, theme, center_text, base_currency):

    # Sort assets to display grouped by asset class
    assets.sort_values(["asset_class_tot_value", "tot_current_value"], inplace=True)

    # Generate shades to distinguish assets
    assets["color"] = assets.groupby("asset_class")["color"].transform(
        lambda color_series: generate_shades(
            color_series.iloc[0],
            len(color_series),
            theme=theme,
        )
    )

    # Format plot labels
    def wrap_labels(label, max_len=15):
        return "<br>".join(textwrap.wrap(label, width=max_len, break_long_words=False))

    assets["asset_wrapped"] = assets["asset"].apply(lambda x: wrap_labels(x))

    # Generate figure
    fig = go.Figure(
        data=[
            go.Pie(
                labels=assets["asset_wrapped"],
                values=assets["tot_current_value"],
                hole=0.7,
                textposition="outside",
                textinfo="label",
                sort=False,
                hovertemplate="%{label}<br>%{value:,.2f} "
                + base_currency
                + "<br>%{percent:.2%}<extra></extra>",
                marker=dict(colors=assets["color"]),
            )
        ]
    )

    # Add annotations
    fig.add_annotation(
        text=f"{center_text:,.2f} {base_currency}",
        font=dict(size=16),
        x=0.5,
        y=0.5,
        showarrow=False,
    )

    fig.update_layout(plotly_layout[theme])
    fig.update_layout(
        showlegend=False,
    )

    graph_div = plot(fig, output_type="div", config=plotly_configuration)

    return graph_div


def generate_accounts_donut(accounts, theme, base_currency):
    # Sort accounts by descending total account value
    accounts.sort_values(["account_total_value"], inplace=True)

    # Format plot lables
    def wrap_labels(label, max_len=15):
        return '<br>'.join(textwrap.wrap(label, width=max_len, break_long_words=False))
    accounts["accounts_wrapped"] = accounts["account"].apply(lambda x: wrap_labels(x))

    # Generate figure
    fig = go.Figure(data=[go.Pie(
        labels=accounts["accounts_wrapped"],
        values=accounts['account_total_value'],
        hole=0.6,
        textinfo='none',
        hovertemplate='%{label}<br>%{value:,.2f} ' + base_currency + '<br>%{percent:.2%}<extra></extra>',
        marker=dict(colors=accounts[f"hsl_{theme}_background"]),
    )])

    # Set plot style
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        height=210,
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=0.95,
        ))

    fig.update_layout(plotly_layout[theme])

    graph_div = plot(fig, output_type='div', config=plotly_configuration)

    return graph_div


def generate_accounts_country_donut(accounts_country, theme, base_currency):
    # Sort countries by descending total asset value of related accounts
    accounts_country.sort_values(["account_total_value"], inplace=True)

    # Format plot lables
    def wrap_labels(label, max_len=15):
        return '<br>'.join(textwrap.wrap(label, width=max_len, break_long_words=False))
    accounts_country["accounts_country_wrapped"] = accounts_country["account_country"].apply(lambda x: wrap_labels(x))

    # Generate figure
    fig = go.Figure(data=[go.Pie(
        labels=accounts_country["accounts_country_wrapped"],
        values=accounts_country['account_total_value'],
        hole=0.6,
        textinfo='none',
        sort=False,
        hovertemplate='%{label}<br>%{value:,.2f} ' + base_currency + '<br>%{percent:.2%}<extra></extra>',
        marker=dict(colors=["#2ab668", "#3255a4"]),
    )])

    # Set plot style
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        height=210,
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=0.95,
        ))

    fig.update_layout(plotly_layout[theme])

    graph_div = plot(fig, output_type='div', config=plotly_configuration)

    return graph_div


def generate_earnings_barplot(grouped_df, theme, base_currency):
    # Extract unique entities
    entities = grouped_df[["entity", "color"]].drop_duplicates()

    # Format month strings
    grouped_df["month_str"] = grouped_df["month"].apply(
        lambda x: pd.Timestamp(x).strftime("%b %Y")
    )

    # Prepare traces for barplot
    data = []
    for _, (entity, color) in entities.iterrows():
        grouped_df_entity = grouped_df[grouped_df["entity"] == entity]
        max_amount = grouped_df_entity["amount"].max()

        # Bar trace for the entity
        trace = go.Bar(
            x=grouped_df_entity["month_str"],
            y=grouped_df_entity["amount"],
            name=entity,
            marker_color=color,
            marker_line_width=0,  # Remove bar outline
            marker=dict(cornerradius="100%"),
            hovertemplate="%{y:,.2f} " + base_currency + "<extra></extra>",
        )
        data.append(trace)

    # Generate barplot
    fig = go.Figure(data=data)

    fig.update_layout(plotly_layout[theme])

    # Set style
    fig.update_layout(
        barmode="group",
        margin=dict(l=20, r=20, t=20, b=20),  # Reduced margins
        bargap=0.4,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.6,  # gap between bars of the same location coordinate.
        showlegend=False,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True, zeroline=False, zerolinewidth=1, showgrid=True),
        margin_pad=10,
        height=370,
    )

    div = plot(
        fig,
        output_type="div",
        config={**plotly_configuration, "scrollZoom": False, "displayModeBar": False},
    )

    return div
