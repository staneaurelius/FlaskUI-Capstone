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
    X = cat_order.index
    Y = cat_order['Total']
    my_colors = 'rgbkymc'

    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    plt.barh(X, Y, color = my_colors)
    plt.savefig('cat_order.png', bbox_inches="tight") 

    # Convert matplotlib PNG to base64 to be able to display it in html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    X = df2['Reviews'].values
    Y = df2['Rating'].values
    area = playstore['Installs'].values/10000000
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()

    plt.scatter(x = X, y = Y, s = area, alpha = 0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    X = (df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()

    plt.hist(X, bins = 100, density = True,  alpha = 0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Bar Plot
    content_rating = df2.groupby('Content Rating').mean()[['Installs']].sort_values(by = 'Installs', ascending = False)
    content_rating['Installs'] /= 1000

    fig = plt.figure(figsize=(6,9))
    fig.add_subplot()
    plt.bar(content_rating.index, content_rating['Installs'])
    plt.xticks(rotation = 45)

    plt.xlabel('Size')
    plt.ylabel('Average Install (Thousand)')
    plt.savefig('rating_installs.png', bbox_inches = 'tight')

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]

    # Add plot results to render_template()
    return render_template('index.html', stats = stats, result = result, result2 = result2, 
                            result3 = result3, result4 = result4)

if __name__ == "__main__": 
    app.run(debug=True)