from dash import Dash, html, dcc, Input, Output, callback
import json
import pandas as pd
import plotly.express as px
from urllib.request import urlopen

pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/laucnty16.csv')

customers = pd.read_csv('olist_customers_dataset.csv')
location = pd.read_csv('olist_geolocation_dataset.csv')
items = pd.read_csv('olist_order_items_dataset.csv')
payments = pd.read_csv('olist_order_payments_dataset.csv')
reviews = pd.read_csv('olist_order_reviews_dataset.csv')
orders = pd.read_csv('olist_orders_dataset.csv')
products = pd.read_csv('olist_products_dataset.csv')
translation = pd.read_csv('product_category_name_translation.csv')
sellers = pd.read_csv('olist_sellers_dataset.csv')

goods = products.merge(items, on='product_id')
goods = goods.merge(orders, on='order_id')
goods = goods.merge(customers, on='customer_id')
goods = goods.merge(sellers, on='seller_id')
goods = goods.merge(translation, on='product_category_name')

# fig.update_layout(
#     plot_bgcolor=colors['background'],
#     paper_bgcolor=colors['background'],
#     font_color=colors['text']
# )

dates = sorted(pd.to_datetime(goods['order_purchase_timestamp']).unique())
df_dates = sorted(pd.to_datetime(goods['order_purchase_timestamp']).dt.to_period('M').unique())

date_selector = dcc.RangeSlider(
    id='range-slider',
    min=0,
    max=len(dates),
    value=[0, len(dates) - 1],
    marks={i * 4200: str(date) for i, date in enumerate(df_dates)}
)

names_state = goods['seller_state'].unique()
options_state = []
for k in names_state:
    options_state.append({'label': k, 'value': k})

state_selector = dcc.Dropdown(
    id='state-selector',
    options=options_state,
    value=[names_state[0]],
    multi=True
)

names_status = goods['order_status'].unique()
options_status = []
for k in names_status:
    options_status.append({'label': k, 'value': k})

status_selector = dcc.Dropdown(
    id='status-selector',
    options=options_status,
    value=[names_status[0]],
    multi=True
)

names_group = ['sellers', 'customers']
options_group = []
for k in names_group:
    options_group.append({'label': k, 'value': k})

group_selector = dcc.Dropdown(
    id='group-selector',
    options=options_group,
    value=[names_group[0]],
    multi=False
)

with urlopen(
        "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
) as response:
    brazil = json.load(response)

# Since the database doesn't have an ID or feature using which values will be mapped between the coordinate/shape database and soybean database, we are adding an ID ourselves.
for feature in brazil["features"]:
    feature["id"] = feature["properties"]["sigla"]

df = goods.groupby('customer_state').agg(number_of_customers=('customer_id', 'nunique')).reset_index()
for feature in brazil["features"]:
    if not (df['customer_state'] == feature["properties"]["sigla"]).any():
        df.loc[len(df.index)] = [feature["properties"]["sigla"], 0]
fig = px.choropleth(df, geojson=brazil, locations='customer_state',
                    color='number_of_customers',
                    color_continuous_scale="Viridis",
                    range_color=(0, df['number_of_customers'].max()),
                    hover_data=["customer_state", "number_of_customers"]
                    )
fig.update_geos(fitbounds="locations", visible=False)

app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Task 4', style={'textAlign': 'center', 'color': '#7FBBFF', 'fontsize': 30}),
    html.Div(children='Choose states:', style={'fontSize': 20}),
    html.Div(state_selector),
    html.Div(date_selector),
    html.Div(children='Choose order status:', style={'fontSize': 20}),
    html.Div(status_selector),
    html.Div([
        html.Div([
            dcc.Markdown(children='Distribution for sellers', style={'fontSize': 24}),
            dcc.Graph(
                id='graph-1',
            ),
        ]),
        html.Div([
            dcc.Markdown(children='Distribution for customers', style={'fontSize': 24}),
            dcc.Graph(
                id='graph-2',
            ),
        ])
    ], style={'columnCount': 2, 'align': 'center'}),
    html.H1(children='Tasks 5-6', style={'textAlign': 'center', 'color': '#7FBBFF', 'fontsize': 30}),
    html.Div(children='Choose sellers or customers:', style={'fontSize': 20}),
    html.Div(group_selector),
    dcc.Graph(
        id='graph-3',
        # clickData={'points': [{'location': 'SP'}]}
    )
])


@app.callback(
    Output('graph-1', 'figure'),
    [Input('range-slider', 'value'),
     Input('state-selector', 'value'),
     Input('status-selector', 'value'),
     Input('graph-3', 'clickData')]
)
def update_fig_1(date, state, status, clickData):
    if clickData:
        state = clickData['points'][0]['location']
        new_goods = goods[(pd.to_datetime(goods['order_purchase_timestamp']) >= dates[int(date[0])]) & (
                pd.to_datetime(goods['order_purchase_timestamp']) <= dates[int(date[1])]) &
                          (goods['seller_state'] == state) &
                          ((goods['order_status']).isin(status))]
    else:
        new_goods = goods[(pd.to_datetime(goods['order_purchase_timestamp']) >= dates[int(date[0])]) & (
                pd.to_datetime(goods['order_purchase_timestamp']) <= dates[int(date[1])]) &
                          ((goods['seller_state']).isin(state)) &
                          ((goods['order_status']).isin(status))]
    new_goods = new_goods.groupby(['seller_state', 'product_category_name_english']).agg(
        {'product_id': 'count'}).reset_index()
    new_fig = px.bar(new_goods, x=new_goods.product_category_name_english, y=new_goods.product_id, color='seller_state',
                     labels={'seller_state': 'Seller state'})
    new_fig.update_xaxes(title_text="Product category name")
    new_fig.update_yaxes(title_text="Number of selled products")
    return new_fig


@app.callback(
    Output('graph-2', 'figure'),
    [Input('range-slider', 'value'),
     Input('state-selector', 'value'),
     Input('status-selector', 'value'),
     Input('graph-3', 'clickData')]
)
def update_fig_2(date, state, status, clickData):
    if clickData:
        state = clickData['points'][0]['location']
        new_goods = goods[(pd.to_datetime(goods['order_purchase_timestamp']) >= dates[int(date[0])]) & (
                pd.to_datetime(goods['order_purchase_timestamp']) <= dates[int(date[1])]) &
                          (goods['customer_state'] == state) &
                          ((goods['order_status']).isin(status))]
    else:
        new_goods = goods[(pd.to_datetime(goods['order_purchase_timestamp']) >= dates[int(date[0])]) & (
                pd.to_datetime(goods['order_purchase_timestamp']) <= dates[int(date[1])]) &
                          ((goods['customer_state']).isin(state)) &
                          ((goods['order_status']).isin(status))]
    new_goods = new_goods.groupby(['customer_state', 'product_category_name_english']).agg(
        {'product_id': 'count'}).reset_index()
    new_fig = px.bar(new_goods, x=new_goods.product_category_name_english, y=new_goods.product_id,
                     color='customer_state', labels={'customer_state': 'Customer state'})
    new_fig.update_xaxes(title_text="Product category name")
    new_fig.update_yaxes(title_text="Number of buyed products")
    return new_fig


@app.callback(
    Output('graph-3', 'figure'),
    [Input('range-slider', 'value'),
     Input('status-selector', 'value'),
     Input('group-selector', 'value'),
     Input('graph-3', 'clickData')]
)
def update_fig_3(date, status, group, clickData):
    if group == 'sellers':
        if clickData:
            selected_state = clickData['points'][0]['location']
            new_goods = goods[(pd.to_datetime(goods['order_purchase_timestamp']) >= dates[int(date[0])]) & (
                    pd.to_datetime(goods['order_purchase_timestamp']) <= dates[int(date[1])]) &
                              (goods['seller_state'] == selected_state) &
                              ((goods['order_status']).isin(status))]
        else:
            new_goods = goods[(pd.to_datetime(goods['order_purchase_timestamp']) >= dates[int(date[0])]) & (
                    pd.to_datetime(goods['order_purchase_timestamp']) <= dates[int(date[1])]) &
                              ((goods['order_status']).isin(status))]
        df = new_goods.groupby('seller_state').agg(number_of_sellers=('seller_id', 'nunique')).reset_index()
        for feature in brazil["features"]:
            if not (df['seller_state'] == feature["properties"]["sigla"]).any():
                df.loc[len(df.index)] = [feature["properties"]["sigla"], 0]
        new_fig = px.choropleth(df, geojson=brazil, locations='seller_state',
                                color_continuous_scale="Viridis",
                                color='number_of_sellers',
                                range_color=(0, df['number_of_sellers'].max()),
                                hover_data=["seller_state", "number_of_sellers"]
                                )
    else:
        if clickData:
            selected_state = clickData['points'][0]['location']
            new_goods = goods[(pd.to_datetime(goods['order_purchase_timestamp']) >= dates[int(date[0])]) & (
                    pd.to_datetime(goods['order_purchase_timestamp']) <= dates[int(date[1])]) &
                              (goods['customer_state'] == selected_state) &
                              ((goods['order_status']).isin(status))]
        else:
            new_goods = goods[(pd.to_datetime(goods['order_purchase_timestamp']) >= dates[int(date[0])]) & (
                    pd.to_datetime(goods['order_purchase_timestamp']) <= dates[int(date[1])]) &
                              ((goods['order_status']).isin(status))]
        df = new_goods.groupby('customer_state').agg(number_of_customers=('customer_id', 'nunique')).reset_index()
        for feature in brazil["features"]:
            if not (df['customer_state'] == feature["properties"]["sigla"]).any():
                df.loc[len(df.index)] = [feature["properties"]["sigla"], 0]
        new_fig = px.choropleth(df, geojson=brazil, locations='customer_state',
                                color='number_of_customers',
                                color_continuous_scale="Viridis",
                                range_color=(0, df['number_of_customers'].max()),
                                hover_data=["customer_state", "number_of_customers"]
                                )
    return new_fig


if __name__ == '__main__':
    app.run_server(debug=True)  # Р·Р°РїСѓСЃРєР°РµРј СЃРµСЂРІРµСЂ