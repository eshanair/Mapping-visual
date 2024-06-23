from flask import Flask, render_template
import folium
from folium.plugins import StripePattern
import geopandas as gpd
import pandas as pd
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Set up your paths based on where the data is on your local filesystem
    abo_file = 'static/js/womens.csv'
    tam_file = 'static/js/tampontax.csv'
    shp_file = 'map/cb_2018_us_state_5m.shp'

    # Load the data
    data = pd.read_csv(abo_file, index_col='States')
    data1 = pd.read_csv(tam_file, index_col='States')
    us_map = gpd.read_file(shp_file)
    merged = us_map.set_index('NAME').join(data)
    merged1 = us_map.set_index('NAME').join(data1)
    print(merged.columns)
    print(merged1.columns)
    
    # Create the Folium map
    m = folium.Map(location=[37, -95], zoom_start=4)
    
    # Setup choropleth layer
    folium.Choropleth(
        geo_data=merged.__geo_interface__,
        name='choropleth',
        data=merged,
        columns=[merged.index, 'Women'],
        key_on='feature.id',
        fill_color='Purples',
        fill_opacity=0.7,
        line_opacity=0.5,
        legend_name='Percentage of Women in Legislature'
    ).add_to(m)

    print(merged[['Women']].isnull().any())

    # Add custom legend
    legend_html = '''
    <div style="position: fixed; bottom: 20px; left: 20px; width: 250px; height: 200px;
        background-color: rgba(255, 255, 255, 0.8); z-index:9999; font-size:14px; padding: 10px; border-radius: 10px;">
    <p><strong>Legend:</strong></p>
    <hr>
    <p><div style="background:purple;width:20px;height:20px;display:inline-block;margin-right:5px;"></div>Women in Legislature (%)</p>
    <p><div style="background:black;width:20px;height:20px;display:inline-block;margin-right:5px;"></div>Abortion Illegal</p>
    <p><div style="background:navy;width:20px;height:20px;display:inline-block;margin-right:5px;"></div>Tampon Tax Imposed</p>
    </div>
    '''

    m.get_root().html.add_child(folium.Element(legend_html))
    folium.GeoJson(
    merged[merged['Legality'] == 0],
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': '#000080',
        'weight': 0.2,
        'opacity': 0.5,
        'fillOpacity': 0.5,
        'fillPattern': StripePattern(angle=45, space_ratio=0.1),
        'dashArray': '5, 5'
        }
    ).add_to(m)

    navy_stripe = StripePattern(angle=-45, opacity=.7, color='navy', space_ratio=0.2)
    navy_stripe.add_to(m)

    black_stripe = StripePattern(angle=45, opacity=.7, color='black', space_ratio=0.2)
    black_stripe.add_to(m)

    # Assuming 'Legality' column represents whether abortion is legal (1 for legal, 0 for illegal)
    folium.GeoJson(
        merged[merged['Legality'] == 0],
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'black',
            'weight': .5,
            'opacity': 1,
            'fillOpacity': 0.7,
            'fillPattern': black_stripe
        }
    ).add_to(m)

    # Assuming 'Tampon' column represents tampon tax (1 for exist, 0 for not exist)
    folium.GeoJson(
        merged1[merged1['Tampon'] == 1],
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'navy',
            'weight': .5,
            'opacity': 1,
            'fillOpacity': 0.7,
            'fillPattern': navy_stripe
        }
    ).add_to(m)

    merged_final = us_map.set_index('NAME').join(data, rsuffix='_abo')
    merged_final = merged_final.join(data1, rsuffix='_tampon')

    folium.GeoJson(
        merged_final,
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'green',
            'weight': 0.5,
            'opacity': 0.5,
            'fillOpacity': 0.5,
            'dashArray': '5, 5'
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=['Code', 'Women', 'Legality', 'Tampon'],
            aliases=['State', '% Women in Legislature', 'Abortion Legality', 'Tampon Tax'],
            labels=True,
            sticky=True
        )
    ).add_to(m)

    folium.GeoJson(
        merged,
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'blue',
            'weight': 0.5,
            'opacity': 0.5,
            'fillOpacity': 0.5,
            'dashArray': '5, 5'
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=['Code', 'Women', 'Legality'],
            aliases=['State', '% Women in Legislature', 'Abortion Legality'],
            labels=True,
            sticky=True
        )
    ).add_to(m)

    # Save the map to an HTML file
    map_path = os.path.join('static', 'maps', 'map.html')
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    m.save(map_path)

    # Render the template
    return render_template('index.html', map_path=map_path)

if __name__ == '__main__':
    app.run(debug=True)
