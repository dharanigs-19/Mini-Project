import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="My streamlit Dashboard", page_icon="✈️", layout="wide")

st.title("✈️Flight Trackers Analytics")

def load_data(query):
    conn = sqlite3.connect("mini (3).db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.markdown(
    """
    <style>
    /* Main app background */
    .stApp {
        background-color: #334155;  /* bright slate */
        color: #ffffff;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
    }

    /* Sidebar text */
    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }

    /* Titles */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 700;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #0f172a;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    }

    /* Metric labels */
    div[data-testid="metric-container"] label {
        color: #c7d2fe !important;
        font-size: 0.9rem;
    }

    /* Metric values */
    div[data-testid="metric-container"] div {
        color: #ffffff !important;
        font-size: 2rem;
        font-weight: 800;
    }

    /* Dataframe container */
    div[data-testid="stDataFrame"] {
        background-color: white;
        padding: 15px;
        border-radius: 14px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
    }

    /* Radio buttons */
    .stRadio label {
        color: #e5e7eb !important;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.sidebar.title("✈️ Flight Dashboard")
page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Search & Filter Flights",
        "Airport Details",
        "Delay Analysis",
        "Route Leaderboards",
    ],
)

if page == "Overview":
    st.title("📊 Flight Operations Overview")
    col1, col2, col3 = st.columns(3,gap="large")
    total_airports = load_data("select count(*) as Total_Airports from airport")["Total_Airports"]
    total_flights = load_data("select count(*) as Total_Flights from flight")["Total_Flights"]
    avg_delay = load_data("select round(avg(avg_delay_min), 2) as Average_Delay from delay")["Average_Delay"]

    col1.metric("✈️Total Airports", total_airports)
    col2.metric("Total Flights", total_flights)
    col3.metric("Average Delay (min)", avg_delay)

elif page == "Search & Filter Flights":
    st.title("🔍 Search & Filter Flights")
    flight_number = st.text_input("Flight Number")
    airline_code = st.text_input("airline_code")
    status = st.selectbox(
        "status", ["All", "Scheduled", "Delayed", "Cancelled", "Departed", "Arrived", "Unknown"]
    )

    query = """
        select flight.flight_number, flight.airline_code, flight.origin_iata,
        flight.destination_iata, flight.status
        from flight left join aircraft on flight.aircraft_registration = aircraft.registration
        where 1=1
    """

    if flight_number:
        query += f" and flight.flight_number LIKE '%{flight_number}%'"
    if airline_code:
        query += f" and flight.airline_code LIKE '%{airline_code}%'"
    if status != "All":
        query += f" and flight.status = '{status}'"

    df = load_data(query)
    st.dataframe(df,use_container_width=True)

elif page == "Airport Details":
    st.title("🏢 Airport Details")

    airport_details=load_data("select iata_code,name,city,country,continent,latitude,longitude,timezone from airport")
    st.dataframe(airport_details,use_container_width=True)

    st.divider()
    st.subheader("✈️ Linked Flights")

    linked_flights = load_data(f"""
            select flight.flight_number, flight.origin_iata, flight.destination_iata, flight.status, aircraft.model as aircraft_model
            from flight 
            left join aircraft on flight.aircraft_registration = aircraft.registration
        """)
        
    if not linked_flights.empty:
       st.dataframe(linked_flights,use_container_width=True)
    else:
       st.info("No linked flights found for this airport.")

elif page == "Delay Analysis":
    st.title("🏢 Delay Analysis")
    delay_data=load_data("""select airport_iata, avg(avg_delay_min) as Average_Delay,
                (sum(delayed_flights) * 100.0 / sum(total_flights)) as Delay_Percentage from delay group by airport_iata""")
   
    num_airports = st.slider("Select number of top airports to display", 10, 190, 10)
    avg_delay_data = delay_data.nlargest(num_airports, "Average_Delay")
    pct_delay_data = delay_data.nlargest(num_airports, "Delay_Percentage")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Delay by Airport")
        fig, ax = plt.subplots(figsize=(6, 8))
        sns.barplot(
            data=avg_delay_data,
            x="Average_Delay",
            y="airport_iata",
            ax=ax,
        )
        st.pyplot(fig)

    with col2:
        st.subheader("Delay Percentage by Airport")
        fig, ax = plt.subplots(figsize=(6, 8))
        sns.barplot(
            data=pct_delay_data,
            x="Delay_Percentage",
            y="airport_iata",
            ax=ax,
        )
        st.pyplot(fig)
    sns.set_style("darkgrid")
    plt.rcParams["axes.facecolor"] = "#111827"
    plt.rcParams["figure.facecolor"] = "#111827"
    plt.rcParams["text.color"] = "white"
    plt.rcParams["axes.labelcolor"] = "white"
    plt.rcParams["xtick.color"] = "white"
    plt.rcParams["ytick.color"] = "white"


elif page == "Route Leaderboards":
    st.title("🏆 Route Leaderboards")

    st.subheader("Busiest Routes - Top 20")
    busiest_routes = load_data("""
        select origin_iata, destination_iata, count(*) as flights
        from flight
        group by origin_iata, destination_iata
        order by flights desc limit 20
    """)
    st.dataframe(busiest_routes, use_container_width=True)

    st.subheader("Most Delayed Airports - Top 20")
    delayed_airports = load_data("""select airport_iata,avg_delay_min as Avg_Delay_minutes,
           total_flights as Total_Flights from delay order by Avg_Delay_minutes desc limit 20
    """)
    st.dataframe(delayed_airports, use_container_width=True)
