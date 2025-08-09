plotly_configuration = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["toImage"],
    "responsive": True,
}

opacity = {"dark": 0.6, "light": 0.725}

plotly_layout = {
    "light": {
        "font": {
            "color": "rgb(80,80,80)",
            "family": "Inter, sans-serif",
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "yaxis": {"gridcolor": "rgb(220,220,220)"},
        "hoverlabel": {
            "bgcolor": "rgb(180, 180, 180)",
            "bordercolor": "rgba(0,0,0,0)",
            "font": {
                "family": "Inter, sans-serif",
                "color": "rgb(80,80,80)",
            },
        },
    },
    "dark": {
        "font": {
            "color": "rgb(255,255,255)",
            "family": "Inter, sans-serif",
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "yaxis": {"gridcolor": "rgb(50,50,50)"},
        "hoverlabel": {
            "bgcolor": "rgb(80, 80, 80)",
            "bordercolor": "rgba(0,0,0,0)",
            "font": {
                "family": "Inter, sans-serif",
                "color": "rgb(255,255,255)",
            },
        },
    },
}
