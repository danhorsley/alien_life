import streamlit as st
import pandas as pd
from starmap import *


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
# selected_types = st.multiselect("Star Spectral Type", options=df['st_spectype'].dropna().unique(), default=[])

# ── Filters ────────────────────────────────────────────────────────────────

st.subheader("Filters")
radii = st.slider("Planet Radius (Earth radii)", 0.1, 20.0, (0.5,5.0))
max_dist = st.slider("Distance from the Sun (pc)", 10, 1000, (10,200))
temp_range = st.slider("Planet Equilibrium Temp (K)", 100, 600, (200, 400))

# Apply the non-spectral filters
df_pre_filt = df[
    (df['pl_rade'].between(*radii)) &
    (df['sy_dist'].between(*max_dist)) &
    (df['pl_eqt'].between(*temp_range))
]

#computing available spectral types for filtering


available_types = sorted(df_pre_filt['st_spectype'].dropna().unique())
# If no data left → show message or empty list
if len(available_types) == 0:
    available_types = []
    st.info("No stars match the current radius / distance / temp filters.")

spectral_groups = st.multiselect(
    "Star Spectral Group",
    options=["F-type", "G-type", "K-type", "M-type", "Giants / Evolved", "Other"],
    default=["K-type", "M-type"]  # defaults for exoplanets
)
with st.expander("Goldilocks Zone (Habitable Zone) Quick Guide", expanded=False):
    st.markdown(f"""
    The **habitable zone** is where liquid water could exist on a planet's surface (rough rules of thumb for main-sequence stars):

    - **F-type** (hotter stars): ~1.0–2.5 AU from star
    - **G-type** (Sun-like): ~0.9–1.4 AU
    - **K-type** (orange dwarfs): ~0.2–0.8 AU
    - **M-type** (red dwarfs): ~0.01–0.1 AU (very close orbits!)

    Your planet equilibrium temp filter set to ({temp_range[0]}–{temp_range[1]} K at the moment) already proxies this somewhat — Earth-like ~255 K, but atmospheres/greenhouse push real HZ outward.
    """)

mask = pd.Series(False, index=df_pre_filt.index)

if "F-type" in spectral_groups:
    mask |= df_pre_filt['st_spectype'].str.upper().str.startswith('F')
if "G-type" in spectral_groups:
    mask |= df_pre_filt['st_spectype'].str.upper().str.startswith('G')
if "K-type" in spectral_groups:
    mask |= df_pre_filt['st_spectype'].str.upper().str.startswith('K')
if "M-type" in spectral_groups:
    mask |= df_pre_filt['st_spectype'].str.upper().str.startswith('M')
if "Giants / Evolved" in spectral_groups:
    mask |= df_pre_filt['st_spectype'].str.contains('III|IV|giant|evolved', case=False, na=False)
if "Other" in spectral_groups:
    mask |= ~df_pre_filt['st_spectype'].str.startswith(('F', 'G', 'K', 'M'), na=False) & ~df_pre_filt['st_spectype'].str.contains('III|IV|giant|evolved', case=False, na=False)

selected_types = df_pre_filt.loc[mask, 'st_spectype'].dropna().unique()

# Final filtered df: apply spectral type on top of pre-filter
if selected_types.any():
    df_filt = df_pre_filt[mask]
else:
    df_filt = df_pre_filt.copy()  

st.caption(f"Showing {len(df_filt)} host stars after all filters")

# ── 3D Star Map ─────────────────────────────────────────────────────────────

st.subheader("3D Interactive Star Map")
fig = create_starmap(df_filt)
st.plotly_chart(fig, use_container_width=True)