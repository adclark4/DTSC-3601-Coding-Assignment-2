# ---
# lambda-test: false  # auxiliary-file
# ---
# ## Demo Streamlit application.
#
# This application is the example from https://docs.streamlit.io/library/get-started/create-an-app.
#
# Streamlit is designed to run its apps as Python scripts, not functions, so we separate the Streamlit
# code into this module, away from the Modal application code.

def main():
    import numpy as np
    import pandas as pd
    import streamlit as st
    import plotly.express as px
    import os
    from supabase import create_client, Client
    from typing import Optional

    st.title("Uber pickups in NYC!")

    DATE_COLUMN = "date/time"
    DATA_URL = (
        "https://s3-us-west-2.amazonaws.com/"
        "streamlit-demo-data/uber-raw-data-sep14.csv.gz"
    )

    @st.cache_data
    def load_data(nrows):
        data = pd.read_csv(DATA_URL, nrows=nrows)

        def lowercase(x):
            return str(x).lower()

        data.rename(lowercase, axis="columns", inplace=True)
        data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
        return data

    data_load_state = st.text("Loading data...")
    data = load_data(10000)
    data_load_state.text("Done! (using st.cache_data)")

    if st.checkbox("Show raw data"):
        st.subheader("Raw data")
        st.write(data)

    st.subheader("Number of pickups by hour")
    hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0, 24))[0]
    st.bar_chart(hist_values)

    # Some number in the range 0-23
    hour_to_filter = st.slider("hour", 0, 23, 17)
    filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]

    st.subheader("Map of all pickups at %s:00" % hour_to_filter)
    st.map(filtered_data)

    # NEW: EXTENSIONS

    # Helper columns for new charts
    data["hour"] = data[DATE_COLUMN].dt.hour
    data["minute"] = data[DATE_COLUMN].dt.minute
    data["day_name"] = data[DATE_COLUMN].dt.day_name()
    _day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    data["day_name"] = data["day_name"].astype(
        pd.CategoricalDtype(categories=_day_order, ordered=True)
    )

    # Interactivity: day filter
    day_choice = st.sidebar.selectbox(
        "Filter charts by day",
        options=["All days"] + _day_order,
        index=0
    )
    show_filtered_raw = st.sidebar.checkbox("Show filtered raw (for new charts)")

    # Apply day filter
    if day_choice != "All days":
        data_filtered = data[data["day_name"] == day_choice]
    else:
        data_filtered = data

    if show_filtered_raw:
        st.subheader("Filtered raw data (for new charts)")
        st.write(data_filtered)

    # NEW Chart 1: Pickups by day of week (Plotly)
    st.subheader("Pickups by day of week (interactive)")
    by_day = (
        data_filtered.groupby("day_name", as_index=False)
        .size()
        .rename(columns={"size": "pickups"})
        .sort_values("day_name")
    )
    fig_day = px.bar(
        by_day,
        x="day_name",
        y="pickups",
        labels={"day_name": "Day", "pickups": "Number of pickups"},
    )
    st.plotly_chart(fig_day, use_container_width=True)

    # NEW Chart 2: Minute-by-minute pickups within the selected hour
    st.subheader(f"Minute-by-minute pickups at {hour_to_filter:02d}:00 (interactive)")
    hour_df = data_filtered[data_filtered["hour"] == hour_to_filter]
    by_minute = (
        hour_df.groupby("minute", as_index=False)
        .size()
        .rename(columns={"size": "pickups"})
        .sort_values("minute")
    )
    fig_min = px.line(
        by_minute,
        x="minute",
        y="pickups",
        markers=True,
        labels={"minute": "Minute", "pickups": "Number of pickups"},
    )
    st.plotly_chart(fig_min, use_container_width=True)

    # Supabase section 

    # Connect to Supabase and display data
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    table_name = st.text_input("Table name in Supabase", value="uber_pickups")

    def connect_supabase() -> Optional[Client]:
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                return None
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None

    sb = connect_supabase()
    df_sb = None
    if sb and table_name:
        try:
            res = sb.table(table_name).select("*").limit(1000).execute()
            rows = res.data or []
            if rows:
                df_sb = pd.DataFrame(rows)
        except Exception:
            pass

    # Show dataframe if data is available
    if df_sb is not None and not df_sb.empty:
        st.subheader(f"Data from table '{table_name}'")
        st.dataframe(df_sb, use_container_width=True)

        # Chart generation
        dt_cols = [c for c in df_sb.columns if "time" in c.lower() or "date" in c.lower() or df_sb[c].dtype.kind in ("M",)]
        num_cols = [c for c in df_sb.columns if np.issubdtype(df_sb[c].dtype, np.number)]
        cat_cols = [c for c in df_sb.columns if df_sb[c].dtype == object]

        # Chart by day if datetime column exists
        if dt_cols:
            dc = dt_cols[0]
            try:
                df_tmp = df_sb.copy()
                df_tmp[dc] = pd.to_datetime(df_tmp[dc], errors="coerce")
                df_tmp = df_tmp.dropna(subset=[dc])
                if not df_tmp.empty:
                    by_day = (
                        df_tmp.set_index(dc)
                        .assign(count=1)["count"]
                        .resample("D")
                        .sum()
                        .reset_index()
                        .rename(columns={dc: "date", 0: "count"})
                    )
                    st.subheader("Rows per day")
                    st.plotly_chart(px.line(by_day, x="date", y="count", markers=True), use_container_width=True)
            except Exception:
                pass

        # Histogram if numeric column exists
        elif num_cols:
            st.subheader(f"Histogram of '{num_cols[0]}'")
            fig = px.histogram(df_sb, x=num_cols[0])
            st.plotly_chart(fig, use_container_width=True)

        # Bar chart if categorical column exists
        elif cat_cols:
            st.subheader(f"Top categories of '{cat_cols[0]}'")
            top_cat = df_sb[cat_cols[0]].value_counts().reset_index()
            top_cat.columns = [cat_cols[0], "count"]
            st.plotly_chart(px.bar(top_cat.head(20), x=cat_cols[0], y="count"), use_container_width=True)



if __name__ == "__main__":
    main()
