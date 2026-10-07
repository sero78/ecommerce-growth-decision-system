import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title='E-Commerce Growth Decision System', page_icon='📈', layout='wide')

DATA = Path(__file__).parent / 'demo_ecommerce_data.csv'

REQUIRED_COLUMNS = ['date','product','category','revenue','orders','sessions','product_views','add_to_cart','checkout','price','discount_pct','margin','campaign']

@st.cache_data
def load_demo_data():
    return pd.read_csv(DATA, parse_dates=['date'])

COLUMN_ALIASES = {
    'date':['date','day','event_date'], 'product':['product','product_name','item_name'],
    'category':['category','product_category','item_category'], 'revenue':['revenue','sales','sales_amount','item_revenue'],
    'orders':['orders','purchases','transactions'], 'sessions':['sessions','visits'],
    'product_views':['product_views','views','item_views'], 'add_to_cart':['add_to_cart','adds_to_cart','cart_adds'],
    'checkout':['checkout','checkouts','begin_checkout'], 'price':['price','unit_price'],
    'discount_pct':['discount_pct','discount','discount_percent'], 'margin':['margin','gross_margin'],
    'campaign':['campaign','campaign_name','promotion']
}

def normalize_columns(df):
    df = df.copy()
    lookup = {str(c).strip().lower(): c for c in df.columns}
    rename = {}
    for target, aliases in COLUMN_ALIASES.items():
        if target in df.columns:
            continue
        for alias in aliases:
            if alias in lookup:
                rename[lookup[alias]] = target
                break
    return df.rename(columns=rename), rename

def validate_data(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return len(missing) == 0, missing

def quality_checks(df):
    issues=[]
    numeric=['revenue','orders','sessions','product_views','add_to_cart','checkout','price','discount_pct','margin']
    for c in numeric:
        df[c]=pd.to_numeric(df[c], errors='coerce')
    nulls=int(df[REQUIRED_COLUMNS].isna().sum().sum())
    if nulls: issues.append(f'{nulls:,} missing/invalid required values')
    neg=int((df[numeric] < 0).sum().sum())
    if neg: issues.append(f'{neg:,} negative numeric values')
    bad_funnel=int(((df['orders']>df['checkout']) | (df['checkout']>df['add_to_cart']) | (df['add_to_cart']>df['product_views']) | (df['product_views']>df['sessions'])).sum())
    if bad_funnel: issues.append(f'{bad_funnel:,} rows with inconsistent funnel counts')
    dup=int(df.duplicated().sum())
    if dup: issues.append(f'{dup:,} duplicate rows')
    return df, issues

def pct_change(current, previous):
    if previous == 0: return 0.0
    return (current-previous)/previous*100

def money(x):
    return f'₺{x:,.0f}'

st.title('E-Commerce Performance & Growth Decision System')
st.caption('Independent portfolio prototype • Upload-ready • Built for e-commerce decision support')

with st.sidebar:
    st.header('Data source')
    uploaded = st.file_uploader('Upload e-commerce CSV', type=['csv'], help='Use the included demo CSV as a template. Your file must contain the required columns.')
    if uploaded is not None:
        try:
            candidate = pd.read_csv(uploaded)
            candidate, mapped = normalize_columns(candidate)
            ok, missing = validate_data(candidate)
            if not ok:
                st.error('Missing required columns after automatic mapping: ' + ', '.join(missing))
                st.caption('Rename these columns in your CSV or use the demo file as a template.')
                st.stop()
            if mapped:
                st.info('Automatically mapped: ' + ', '.join([f'{a} → {b}' for a,b in mapped.items()]))
            candidate['date'] = pd.to_datetime(candidate['date'], errors='coerce')
            if candidate['date'].isna().any():
                st.error('Some date values could not be read. Use a standard date format such as YYYY-MM-DD.')
                st.stop()
            df = candidate
            source_label = 'Uploaded CSV'
            st.success(f'Loaded {len(df):,} rows from your CSV.')
        except Exception as e:
            st.error(f'Could not read the uploaded CSV: {e}')
            st.stop()
    else:
        df = load_demo_data()
        source_label = 'Built-in synthetic demo data'
        st.info('Using synthetic demo data. Upload a compatible CSV above to analyze another dataset.')

    with st.expander('Required CSV columns'):
        st.code(', '.join(REQUIRED_COLUMNS))
        st.caption('Tip: use demo_ecommerce_data.csv as the template for your own dataset.')

    df, quality_issues = quality_checks(df)
    if quality_issues:
        st.warning('Data quality flags: ' + ' • '.join(quality_issues))
    else:
        st.success('Data quality check passed.')

    weekly_target = st.number_input('Weekly revenue target (TRY)', min_value=1.0, value=500000.0, step=10000.0)

latest = df['date'].max()
prev = latest - pd.Timedelta(days=7)
cur_start = latest - pd.Timedelta(days=6)
prev_start = latest - pd.Timedelta(days=13)
cur = df[(df.date>=cur_start)&(df.date<=latest)].copy()
old = df[(df.date>=prev_start)&(df.date<=prev)].copy()

if cur.empty or old.empty:
    st.error('The dataset needs at least 14 days of data so the last 7 days can be compared with the previous 7 days.')
    st.stop()


# Core KPI calculations
revenue = cur.revenue.sum(); old_revenue = old.revenue.sum()
orders = cur.orders.sum(); old_orders = old.orders.sum()
sessions = cur.sessions.sum(); old_sessions = old.sessions.sum()
conv = orders/sessions*100 if sessions else 0; old_conv = old_orders/old_sessions*100 if old_sessions else 0
aov = revenue/orders if orders else 0; old_aov = old_revenue/old_orders if old_orders else 0
target = weekly_target
achievement = revenue/target*100

with st.sidebar:
    st.divider()
    st.header('Prototype scope')
    st.write('A lightweight decision-support tool for a market owner responsible for sales, conversion, merchandising, pricing and growth.')
    st.markdown(f'**Source:** {source_label}')
    st.markdown('**Period:** Last 7 days vs previous 7 days')
    st.markdown(f'**Latest date:** {latest.date()}')

st.subheader('Executive summary')
rev_delta=pct_change(revenue,old_revenue)
order_delta=pct_change(orders,old_orders)
conv_delta=conv-old_conv
summary_cols=st.columns(4)
summary_cols[0].markdown(f'**Revenue trend**\n\n{rev_delta:+.1f}% vs previous week')
summary_cols[1].markdown(f'**Conversion movement**\n\n{conv_delta:+.2f} pp')
summary_cols[2].markdown(f'**Target gap**\n\n{money(max(target-revenue,0))}')
summary_cols[3].markdown(f'**Data quality**\n\n{"Review flags" if quality_issues else "Passed"}')
st.caption('Management view: identify the largest performance gap first, then use the funnel, product and campaign sections to locate the likely driver.')

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric('Revenue', money(revenue), f'{pct_change(revenue,old_revenue):.1f}%')
c2.metric('Orders', f'{orders:,.0f}', f'{pct_change(orders,old_orders):.1f}%')
c3.metric('Conversion rate', f'{conv:.2f}%', f'{conv-old_conv:+.2f} pp')
c4.metric('Average order value', money(aov), f'{pct_change(aov,old_aov):.1f}%')
c5.metric('Target achievement', f'{achievement:.1f}%', f'{money(target-revenue)} gap' if revenue<target else 'Target beaten')

st.divider()
left,right = st.columns([1.35,1])
with left:
    st.subheader('Sales & growth trend')
    daily = df.groupby('date',as_index=False).agg(revenue=('revenue','sum'),orders=('orders','sum'),sessions=('sessions','sum'))
    fig = px.line(daily, x='date', y='revenue', markers=True, labels={'revenue':'Revenue (TRY)','date':''})
    fig.update_layout(height=340, margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader('Customer funnel')
    funnel_vals = [cur.sessions.sum(),cur.product_views.sum(),cur.add_to_cart.sum(),cur.checkout.sum(),cur.orders.sum()]
    stages=['Sessions','Product views','Add to cart','Checkout','Purchase']
    fig2=go.Figure(go.Funnel(y=stages,x=funnel_vals,textinfo='value+percent initial'))
    fig2.update_layout(height=340, margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig2,use_container_width=True)

st.divider()
st.subheader('Product & merchandising performance')
prod = cur.groupby(['product','category'],as_index=False).agg(
    revenue=('revenue','sum'), orders=('orders','sum'), sessions=('sessions','sum'),
    product_views=('product_views','sum'), price=('price','mean'), discount=('discount_pct','mean'), margin=('margin','sum'))
prod['conversion_rate']=prod.orders/prod.sessions*100
prod['revenue_share']=prod.revenue/prod.revenue.sum()*100
prod['signal']=np.where((prod.sessions>prod.sessions.median())&(prod.conversion_rate<prod.conversion_rate.median()),'High traffic / low conversion',
                np.where(prod.conversion_rate>prod.conversion_rate.quantile(.75),'Strong converter','Monitor'))
show=prod.sort_values('revenue',ascending=False).copy()
show['revenue']=show.revenue.map(money); show['price']=show.price.map(money)
show['conversion_rate']=show.conversion_rate.map(lambda x:f'{x:.2f}%'); show['discount']=show.discount.map(lambda x:f'{x:.0f}%')
st.dataframe(show[['product','category','revenue','orders','conversion_rate','price','discount','signal']],use_container_width=True,hide_index=True)

st.divider()
a,b=st.columns(2)
with a:
    st.subheader('Campaign & pricing view')
    camp=cur.groupby('campaign',as_index=False).agg(revenue=('revenue','sum'),orders=('orders','sum'),margin=('margin','sum'),discount=('discount_pct','mean'))
    camp['margin_rate']=camp.margin/camp.revenue*100
    fig3=px.bar(camp.sort_values('revenue'),x='campaign',y='revenue',text_auto='.2s',hover_data=['orders','discount','margin_rate'])
    fig3.update_layout(height=330,margin=dict(l=10,r=10,t=20,b=10),xaxis_title='',yaxis_title='Revenue (TRY)')
    st.plotly_chart(fig3,use_container_width=True)
with b:
    st.subheader('Category opportunity map')
    cat=cur.groupby('category',as_index=False).agg(revenue=('revenue','sum'),orders=('orders','sum'),sessions=('sessions','sum'),margin=('margin','sum'))
    cat['conversion_rate']=cat.orders/cat.sessions*100
    cat['margin_rate']=cat.margin/cat.revenue*100
    fig4=px.scatter(cat,x='conversion_rate',y='margin_rate',size='revenue',text='category',hover_data=['orders'])
    fig4.update_traces(textposition='top center')
    fig4.update_layout(height=330,margin=dict(l=10,r=10,t=20,b=10),xaxis_title='Conversion rate (%)',yaxis_title='Margin rate (%)')
    st.plotly_chart(fig4,use_container_width=True)

st.divider()
st.subheader('🎯 Recommended actions')
actions=[]
# deterministic, data-derived rules
if conv < old_conv:
    lost = (old_conv-conv)/100*sessions*aov
    actions.append(('HIGH','Conversion','Conversion fell versus the previous week',f'Investigate funnel friction first. At current traffic, recovering the previous conversion rate represents roughly {money(lost)} in revenue opportunity.'))
if achievement < 100:
    actions.append(('HIGH','Growth target',f'Revenue is at {achievement:.1f}% of the weekly target',f'Prioritize high-converting products and targeted campaigns to close the {money(target-revenue)} gap.'))
low=prod[(prod.sessions>prod.sessions.median())&(prod.conversion_rate<prod.conversion_rate.median())].sort_values('sessions',ascending=False)
if len(low):
    p=low.iloc[0]
    actions.append(('MEDIUM','Merchandising',f"{p['product']} has high traffic but only {p['conversion_rate']:.2f}% conversion",'Review product page, price position, size availability and merchandising before buying more traffic.'))
# campaign efficiency
if len(camp):
    weakest=camp.sort_values('margin_rate').iloc[0]
    actions.append(('MEDIUM','Campaign efficiency',f'{weakest.campaign} has the lowest margin rate ({weakest.margin_rate:.1f}%)','Check whether incremental sales justify discount depth; test a narrower promotion or product selection.'))
best=prod.sort_values('conversion_rate',ascending=False).iloc[0]
actions.append(('OPPORTUNITY','Growth experiment',f"{best['product']} is the strongest converter at {best['conversion_rate']:.2f}%",'Test additional visibility or a controlled traffic increase and measure incremental revenue and margin.'))

for priority,area,issue,action in actions[:5]:
    with st.container(border=True):
        st.markdown(f'**{priority} · {area}**')
        st.write(issue)
        st.caption(action)

st.divider()
st.subheader('How this prototype supports an e-commerce market owner')
st.write('The tool turns raw performance data into a compact operating view: target tracking, funnel diagnosis, product prioritization, campaign economics and data-derived next actions. A production version could connect to analytics, commerce and advertising APIs, store history in SQL, automate alerts and support controlled growth experiments.')
st.caption(f'Portfolio prototype — calculations and recommendations are generated from: {source_label}.')
