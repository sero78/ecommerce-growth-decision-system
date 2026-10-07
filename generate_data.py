import pandas as pd, numpy as np
from pathlib import Path
rng=np.random.default_rng(42)
dates=pd.date_range('2026-09-23','2026-10-06')
products=[
('Tailored Blazer','Outerwear',2790,0.08),('Wide Leg Trousers','Bottoms',1590,0.12),('Satin Shirt','Tops',1290,0.18),
('Knit Cardigan','Knitwear',1890,0.10),('Midi Dress','Dresses',2390,0.15),('Basic T-Shirt','Tops',790,0.05),
('Pleated Skirt','Bottoms',1490,0.20),('Trench Coat','Outerwear',3290,0.10)]
campaigns=['Always On','Midweek Edit','Weekend Offer']
rows=[]
for d_i,d in enumerate(dates):
  for p_i,(p,cat,price,disc) in enumerate(products):
    sessions=int(rng.integers(180,650)*(1+0.08*np.sin(d_i/2)))
    # create a current-week conversion softness but product heterogeneity
    base=0.032 + (p_i%4)*0.004
    if d>=pd.Timestamp('2026-09-30'): base-=0.0035
    if p=='Satin Shirt': base-=0.009
    if p=='Basic T-Shirt': base+=0.012
    orders=max(1,int(sessions*max(.012,base+rng.normal(0,.003))))
    views=int(sessions*rng.uniform(.72,.88)); carts=max(orders,int(views*rng.uniform(.075,.12))); checkout=max(orders,int(carts*rng.uniform(.55,.75)))
    campaign=campaigns[(d_i+p_i)%3]
    ddisc=disc + (0.08 if campaign=='Weekend Offer' else 0)
    sell_price=price*(1-ddisc)
    revenue=orders*sell_price
    margin_rate=.46-ddisc*.55 + rng.normal(0,.01)
    margin=revenue*margin_rate
    rows.append([d,p,cat,round(price,2),round(ddisc*100,1),campaign,sessions,views,carts,checkout,orders,round(revenue,2),round(margin,2)])
cols=['date','product','category','price','discount_pct','campaign','sessions','product_views','add_to_cart','checkout','orders','revenue','margin']
pd.DataFrame(rows,columns=cols).to_csv(Path(__file__).parent/'demo_ecommerce_data.csv',index=False)
