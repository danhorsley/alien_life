import streamlit as st
import pandas as pd
import plotly.express as px
import astropy.coordinates as coord
import astropy.units as u

def create_starmap(df_filt: pd.DataFrame,
                   color_by: str = 'st_spectype',
                   size_by: str = 'st_rad',
                   title: str = "3D Interactive Star Map (Heliocentric)") -> px.scatter_3d:
    """
    Creates a 3D scatter plot of host stars from filtered exoplanet data.
    - Converts RA/Dec + distance to Cartesian x/y/z (pc)
    - Color/size toggles via input params
    - Returns Plotly figure for st.plotly_chart
    """
    if df_filt.empty:
        fig = px.scatter_3d(pd.DataFrame(), x=[0], y=[0], z=[0],
                            title="No stars match filters")
        return fig

    # Ensure numeric columns
    for col in ['ra', 'dec', 'sy_dist']:
        if col in df_filt.columns:
            df_filt[col] = pd.to_numeric(df_filt[col], errors='coerce').astype('float64')

    df_plot = df_filt.dropna(subset=['ra', 'dec', 'sy_dist']).copy()

    if df_plot.empty:
        fig = px.scatter_3d(pd.DataFrame(), x=[0], y=[0], z=[0],
                            title="No valid coordinates")
        return fig
    
    #debugging output
    st.write("RA dtype:", df_plot['ra'].dtype, "first values:", df_plot['ra'].head().tolist())
    st.write("Dec dtype:", df_plot['dec'].dtype, "first values:", df_plot['dec'].head().tolist())
    st.write("Dist dtype:", df_plot['sy_dist'].dtype, "first values:", df_plot['sy_dist'].head().tolist())
    st.write("Any NA still present?", df_plot[['ra','dec','sy_dist']].isna().any().any())
    
    # Astropy SkyCoord → Cartesian (x,y,z in pc)
    sky = coord.SkyCoord(
        ra=df_plot['ra'].values * u.deg,           # ← .make sure vector in correct format
        dec=df_plot['dec'].values * u.deg,
        distance=df_plot['sy_dist'].values * u.pc,
        frame='icrs'
    )

    df_plot['x'] = sky.cartesian.x.to(u.pc).value
    df_plot['y'] = sky.cartesian.y.to(u.pc).value
    df_plot['z'] = sky.cartesian.z.to(u.pc).value

    # Color & size columns (with fallbacks)
    color_col = color_by if color_by in df_plot.columns else 'st_spectype'
    size_col  = size_by  if size_by  in df_plot.columns else 'st_rad'

    # 3D Scatter
    fig = px.scatter_3d(
        df_plot,
        x='x', y='y', z='z',
        color=color_col,
        size=size_col,
        hover_name='hostname',
        hover_data=['pl_name', 'sy_dist', 'st_teff', 'st_spectype', 'st_mass', 'st_rad'],
        title=title,
        labels={
            'x': 'X (pc)',
            'y': 'Y (pc)',
            'z': 'Z (pc)'
        },
        opacity=0.8,
        size_max=30
    )

    # Make it look nice
    fig.update_layout(
        scene=dict(
            xaxis_title='X (pc)',
            yaxis_title='Y (pc)',
            zaxis_title='Z (pc)',
            aspectmode='cube',           # equal scale
            bgcolor='rgba(0,0,0,0)'      # transparent bg if dark theme
        ),
        showlegend=True,
        template="plotly_dark",          # or "plotly"
        margin=dict(l=0, r=0, b=0, t=50)
    )

    # Add Sun at origin
    fig.add_scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers',
        marker=dict(size=8, color='yellow', symbol='diamond'),
        name='Sun (origin)',
        hoverinfo='name'
    )

    return fig
    
    