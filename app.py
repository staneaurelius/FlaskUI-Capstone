from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

playstore = pd.read_csv('data/googleplaystore.csv')

# Delete row 10472 because the data is not input in the correct columns
playstore.drop([10472], inplace=True)

playstore.drop_duplicates(subset = 'App', keep = 'first', inplace = True)

playstore.Category = playstore['Category'].astype('category')

playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace(',', ''))
playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace('+', ''))
playstore['Installs'] = playstore['Installs'].astype(int)

# Cleaning Size column
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore['Price'] = playstore['Price'].apply(lambda x: x.replace('$', ''))
playstore['Price'] = playstore['Price'].astype(float)

# Change Review, Size, and Installs data types to Integer
playstore[['Reviews', 'Size', 'Installs']] = playstore[['Reviews', 'Size', 'Installs']].astype(int)

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Statistik
    top_category = pd.crosstab(index = df2['Category'], columns = 'Count'). \
                        sort_values(by = 'Count', ascending = False). \
                        reset_index()

    # stats dictionary is used to save some data that will be displayed in table and value box
    stats = {
        'most_categories' : top_category['Category'][0],
        'total': top_category['Count'][0],
        'rev_table' : df2[['Category', 'App', 'Reviews', 'Rating']]. \
                                                sort_values(by = 'Reviews', ascending = False).\
                                                reset_index().drop(columns = 'index'). \
                                                head(10). \
                                                to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    cat_order = df2.groupby('Category').agg({
    'Category' : 'count'
        }).rename({'Category':'Total'}, axis=1).sort_values(by = 'Total', ascending = False).head()
    my_colors = 'rgbkymc'

    ax = cat_order.plot(kind = 'barh', color = my_colors, legend = False, figsize = (8,3))

    # Convert matplotlib PNG to base64 to be able to display it in html
    figfile = BytesIO()
    plt.savefig(figfile, format='png', bbox_inches = 'tight')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    ax = df2.plot(kind = 'scatter', x = 'Reviews', y = 'Rating', s = df2['Installs'].values/10000000, 
                  alpha = 0.3, figsize = (5,5))
    ax.set_xlabel('Reviews')
    ax.set_ylabel('Rating')

    figfile = BytesIO()
    plt.savefig(figfile, format='png', bbox_inches = 'tight')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    df2['Size'] = df2['Size']/1000000

    ax = df2[['Size']].plot(kind = 'hist', bins = 100, density = True,  alpha = 0.75)
    ax.set_xlabel('Size')
    ax.set_ylabel('Frequency')

    figfile = BytesIO()
    plt.savefig(figfile, format='png', bbox_inches = 'tight')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Bar Plot
    content_rating = df2.groupby('Content Rating').mean()[['Installs']].sort_values(by = 'Installs', ascending = False)
    content_rating['Installs'] /= 1000

    ax = content_rating.plot(kind = 'bar', rot = 45, legend = False, figsize = (6,9))
    ax.set_xlabel('Size')
    ax.set_ylabel('Average Install (Thousand)')

    figfile = BytesIO()
    plt.savefig(figfile, format='png', bbox_inches = 'tight')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]

    # Add plot results to render_template()
    return render_template('index.html', stats = stats, result = result, result2 = result2, 
                            result3 = result3, result4 = result4)

if __name__ == "__main__": 
    app.run(debug=True)