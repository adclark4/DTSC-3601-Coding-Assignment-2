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

    # Extend the dashboard:

    # Prep extra columns once
    data["day_name"] = data[DATE_COLUMN].dt.day_name()
    data["hour"] = data[DATE_COLUMN].dt.hour
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    # Chart 1: Pickups by day of week (interactive)
    st.subheader("Pickups by day of week (interactive)")
    # order the bars Mon→Sun
    by_day = (
        data.groupby("day_name", as_index=False)
            .size()
            .rename(columns={"size": "pickups"})
    )
    by_day["day_name"] = pd.Categorical(by_day["day_name"], categories=day_order, ordered=True)
    by_day = by_day.sort_values("day_name")

    fig_day = px.bar(by_day, x="day_name", y="pickups",
                     labels={"day_name": "Day", "pickups": "# Pickups"})
    st.plotly_chart(fig_day, use_container_width=True)

    # Chart 2: Hourly pickups with filters
    st.subheader("Hourly pickups (filter by day and hour range)")

    # Interactivity: choose a single day (or all) and an hour window
    day_choice = st.selectbox("Filter to a day", ["All days"] + day_order, index=0)
    hr_min, hr_max = st.slider("Hour range", 0, 23, (0, 23))

    # Apply filters without touching the original 'data'
    df_display = data.copy()
    if day_choice != "All days":
        df_display = df_display[df_display["day_name"] == day_choice]
    df_display = df_display[(df_display["hour"] >= hr_min) & (df_display["hour"] <= hr_max)]

    by_hour = (
        df_display.groupby("hour", as_index=False)
                  .size()
                  .rename(columns={"size": "pickups"})
                  .sort_values("hour")
    )

    fig_hour = px.line(by_hour, x="hour", y="pickups", markers=True,
                       labels={"hour": "Hour", "pickups": "# Pickups"})
    st.plotly_chart(fig_hour, use_container_width=True)

if __name__ == "__main__":
    main()