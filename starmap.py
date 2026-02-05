import pandas as pd
import streamlit as st
import plotly.express as px
from poliastro.bodies import Earth, Sun
from poliastro.twobody import Orbit
from poliastro.plotting import OrbitPlotter2D
from astropy.time import Time
import astropy.units as u

def create_startmap(df_filt : pd.DataFrame, selected_planet: str) -> 'px.graph_objs._figure.Figure':
    if not df_filt.empty:
        row = df_filt[df_filt['pl_name'] == selected_planet].iloc[0]

        try:
            # Earth reference orbit (circular at 1 AU)
            earth_orb = Orbit.circular(Sun, 1 * u.AU)

            # Planet orbit from real elements (fallback if missing)
            a = row.get('pl_orbsmax', 1.0) * u.AU
            ecc = row.get('pl_orbeccen', 0.0) * u.one
            inc = row.get('pl_orbincl', 0.0) * u.deg if 'pl_orbincl' in row else 0 * u.deg

            planet_orb = Orbit.from_classical(
                Sun,
                a=a,
                ecc=ecc,
                inc=inc,
                raan=0 * u.deg,    # placeholder
                argp=0 * u.deg,    # placeholder
                nu=0 * u.deg,
                epoch=Time.now()
            )

            # Plot with explicit colors
            plotter = OrbitPlotter2D()
            plotter.plot(earth_orb, label="Earth (1 AU)", color="blue")
            plotter.plot(planet_orb, label=selected_planet, color="orange")

            # Get the Plotly figure object
            fig = plotter._figure  # ← this is the correct attribute (not .fig)

            # Optional: customize
            fig.update_layout(
                title=f"2D Orbit of {selected_planet} (Earth reference)",
                showlegend=True,
                template="plotly_dark"  # or "plotly"
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.warning(f"Couldn't plot orbit for {selected_planet}: {e}")
            st.info("Missing or invalid orbital elements (a, e, i).")
    else:
        st.info("No planets match your filters.")
    
    