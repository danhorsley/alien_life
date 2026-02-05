import streamlit as st
import pandas as pd
import plotly.express as px
import astropy.coordinates as coord
import astropy.units as u

def create_starmap(df_filt: pd.DataFrame,
                   color_by: str = 'st_spectype',
                   size_by: str = 'st_rad',
                   title: str = "Heliocentric 3D Interactive Star Map"
                   ) -> px.scatter_3d:
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
    
    # Aggregate per unique host
    host_agg = {
        'ra': 'first',
        'dec': 'first',
        'sy_dist': 'first',
        'st_spectype': 'first',  # or mode/any if varies (rare)
        'st_teff': 'first',
        'st_mass': 'first',
        'st_rad': 'first',
        # Planet aggregates
        'pl_name': lambda x: ', '.join(sorted(x.dropna().unique())),  # comma-separated unique planet names
        'sy_pnum': 'size',                                       # count of planets
        'disc_year': 'min'                                        # earliest discovery date
        # Add more if needed, e.g. 'pl_rade': list for all radii
    }

    df_hosts = df_plot.groupby('hostname').agg(host_agg).reset_index()
    # 
    
    
    

    df_hosts['fun_blurb'] = df_hosts.apply(generate_blurbs, axis=1)

    df_hosts['blurb'] = df_hosts.apply(generate_blurbs, axis=1)
    
    if df_hosts.empty:
        fig = px.scatter_3d(pd.DataFrame(), x=[0], y=[0], z=[0],
                            title="No valid coordinates")
        return fig
    
    # Astropy SkyCoord → Cartesian (x,y,z in pc)
    sky = coord.SkyCoord(
    ra=df_hosts['ra'].values * u.deg,
    dec=df_hosts['dec'].values * u.deg,
    distance=df_hosts['sy_dist'].values * u.pc,
    frame='icrs'
    )

    df_hosts['x'] = sky.cartesian.x.to(u.pc).value
    df_hosts['y'] = sky.cartesian.y.to(u.pc).value
    df_hosts['z'] = sky.cartesian.z.to(u.pc).value
    
    # Color & size (using host-level cols)
    color_col = color_by if color_by in df_hosts else 'st_spectype'
    size_col  = size_by  if size_by  in df_hosts else 'st_rad'

    # 3D Scatter
    fig = px.scatter_3d(
        df_hosts,
        x='x', y='y', z='z',
        color=color_col,
        size=size_col,
        hover_name='hostname',
        hover_data=[
            'pl_name',           # now aggregated
            'sy_pnum',
            'disc_year',      # format as needed
            'sy_dist',
            'st_teff',
            'st_spectype',
            'st_mass',
            'st_rad'
        ],
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
        margin=dict(l=0, r=0, b=0, t=50),
        title = title
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
    
def add_host_labels(fig: px.scatter_3d, df_hosts: pd.DataFrame,
                    text_col: str = 'hostname',
                    font_size: int = 10,
                    color: str = 'white',
                    position: str = 'top center') -> None:
    """
    Adds a text-only trace for permanent labels next to each host point.
    - Modifies fig in-place.
    - Optional: make toggleable later via a param.
    """
    fig.add_scatter3d(
        x=df_hosts['x'],
        y=df_hosts['y'],
        z=df_hosts['z'],
        mode='text',
        text=df_hosts[text_col],
        textposition=position,             # options: 'top center', 'bottom right', etc.
        textfont=dict(size=font_size, color=color),
        hoverinfo='skip',                  # no extra hover on labels
        showlegend=False                   # no legend entry
    )   
    
# create blurb for click listener on plot
def generate_blurbs(row):
    # Constants (updated Feb 2026: Parker Solar Probe holds ~692,000 km/h record)
    FASTEST_SPEED_KMH = 692000          # Parker Solar Probe peak (Dec 2024 onward)
    HOURS_PER_YEAR = 8760               # approx
    LIGHT_YEAR_KM = 9.46073e12          # exact-ish value
    hostname = row['hostname']
    spt = row.get('st_spectype', 'mysterious').upper()
    num_pl = row['sy_pnum'] if pd.notna(row['sy_pnum']) else 0
    pl_list = row['pl_name'] if pd.notna(row['pl_name']) else "none known yet"
    dist_pc = row['sy_dist']
    dist_ly = dist_pc / 3.08568          # pc to light-years (approx 1 pc = 3.08568 ly)
    
    # Rough travel time (one-way, no relativity or acceleration fanciness)
    distance_km = dist_ly * LIGHT_YEAR_KM
    speed_km_per_year = FASTEST_SPEED_KMH * HOURS_PER_YEAR
    travel_years = int(distance_km / speed_km_per_year) if speed_km_per_year > 0 else "way too long"
    
    # Spectral flavor
    if spt.startswith('M'):
        star_desc = "a chill red dwarf that's basically immortal (trillions of years potential lifespan)"
    elif spt.startswith('K'):
        star_desc = "a cozy orange dwarf — long-lived and pretty forgiving for planets"
    elif spt.startswith('G'):
        star_desc = "a proper Sun-like yellow star (the classic 'Goldilocks' host)"
    elif spt.startswith('F'):
        star_desc = "a bright white-yellow hotshot (shorter life but dazzling)"
    else:
        star_desc = "an intriguing star of type " + spt
    
    # HZ cheek
    hz_status = "probably not — wrong orbit or too extreme" 
    if row.get('potentially_habitable', False):
        hz_status = "At least one might be in the sweet spot for liquid water 🌊 (fingers crossed for aliens)"
    
    blurb = f"""
            **{hostname}**  

            This {star_desc} is approximately {dist_ly:.1f} light-years from us.  

            It has **{num_pl} planet{'s' if num_pl != 1 else ''}** ({pl_list}).  

            Habitable zone? {hz_status}  

            Getting there with today's fastest spacecraft tech (Parker Solar Probe speeds ~692,000 km/h)?  
            Roughly **{travel_years:,} years** one-way. Better bring a really good book... or wait for that warp drive breakthrough. 🚀😅
            """

    return blurb