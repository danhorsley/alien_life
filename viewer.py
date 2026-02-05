import streamlit as st
import pandas as pd


@st.cache_data
def load_planets():
    df = pd.read_parquet("data/planets.parquet")
    date_cols = ['disc_pubdate'] if 'disc_pubdate' in df else []
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    numeric_cols = [
        'pl_rade', 'pl_orbsmax', 'pl_orbper', 'pl_orbeccen', 'pl_eqt',
        'st_teff', 'st_rad', 'st_mass', 'st_met', 'st_logg',
        'sy_dist', 'sy_vmag', 'sy_kmag', 'sy_gaiamag'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        # Ensure Date is date-only (if needed — usually not for this table)
        if 'disc_pubdate' in df.columns:
            df['disc_pubdate'] = pd.to_datetime(df['disc_pubdate']).dt.date
    
    return df

df = load_planets()
selected_types = st.multiselect("Star Spectral Type", options=df['st_spectype'].dropna().unique(), default=[])
min_radius = st.slider("Min Planet Radius (Earth radii)", 0.1, 20.0, 0.5)
max_dist = st.slider("Max Distance (pc)", 10, 1000, 200)
temp_range = st.slider("Planet Equilibrium Temp (K)", 100, 600, (200, 400))
df_filt = df[
    (df['st_spectype'].isin(selected_types) if selected_types else True) &
    (df['pl_rade'] >= min_radius) &
    (df['sy_dist'] <= max_dist) &
    (df['pl_eqt'].between(*temp_range))
] 