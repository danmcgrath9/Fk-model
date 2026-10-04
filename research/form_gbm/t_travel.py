"""Travel (pros' 'the stable has travelled it'): road distance proxy from the horse's training location to today's track,
great-circle km from approximate town coordinates. Stage-2 inputs on the holdout."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
LL={"Cranbourne":(-38.10,145.28),"Pakenham":(-38.07,145.48),"Pakenham 3":(-38.07,145.48),"Flemington":(-37.79,144.91),"Ballarat":(-37.56,143.85),
"Mornington":(-38.22,145.04),"Warrnambool":(-38.38,142.48),"Seymour":(-37.03,145.14),"Geelong":(-38.15,144.36),"Wangaratta":(-36.36,146.31),
"Bendigo":(-36.76,144.28),"Sale":(-38.11,147.07),"Kyneton":(-37.24,144.45),"Swan Hill":(-35.34,143.55),"Stawell":(-37.06,142.78),"Plumpton":(-37.68,144.69),
"Horsham":(-36.71,142.20),"Benalla":(-36.55,145.98),"Kilmore":(-37.30,144.95),"Moe":(-38.17,146.26),"Colac":(-38.34,143.59),"Wodonga":(-36.12,146.89),
"Freshwater Creek":(-38.27,144.19),"Euroa":(-36.75,145.57),"Echuca":(-36.13,144.75),"Caulfield":(-37.88,145.04),"Mildura":(-34.19,142.16),
"Ararat":(-37.28,142.93),"Hamilton":(-37.74,142.02),"Bairnsdale":(-37.83,147.61),"Traralgon":(-38.20,146.54),"Werribee":(-37.90,144.66),
"Mornington Peninsula":(-38.3,145.1),"Macedon":(-37.42,144.56),"Yarra Glen":(-37.66,145.37),"Terang":(-38.24,142.92),"Tatura":(-36.44,145.23),
"Casterton":(-37.58,141.40),"Donald":(-36.37,142.98),"Avoca":(-37.09,143.47),"Murtoa":(-36.62,142.47),"Nhill":(-36.33,141.65),"Kerang":(-35.73,143.92),
"Camperdown":(-38.23,143.15),"Coleraine":(-37.60,141.69),"Mortlake":(-38.08,142.81),"Penshurst":(-37.87,142.29),"Dunkeld":(-37.65,142.34),
"Edenhope":(-37.04,141.29),"Great Western":(-37.15,142.86),"Burrumbeet":(-37.49,143.65),"Hanging Rock":(-37.33,144.59),"Stony Creek":(-38.58,146.03),
"Towong":(-36.12,147.97),"Wycheproof":(-36.08,143.23),"Manangatang":(-35.05,142.88),"Warracknabeal":(-36.25,142.39),"St Arnaud":(-36.62,143.26),
"Yarra Valley":(-37.66,145.37),"Moonee Valley":(-37.77,144.93),"Sandown Hillside":(-37.95,145.16),"Sandown Lakeside":(-37.95,145.16),"Caulfield Heath":(-37.88,145.04),
"Pakenham Park":(-38.07,145.48),"Pakenham Synthetic":(-38.07,145.48),"Ballarat Synthetic":(-37.56,143.85),
"Randwick":(-33.90,151.23),"Warwick Farm":(-33.91,150.94),"Rosehill":(-33.82,151.02),"Canberra":(-35.28,149.13),"Albury":(-36.08,146.92),"Wagga":(-35.11,147.37),
"Murray Bridge":(-35.12,139.27),"Morphettville":(-34.98,138.54),"Mount Gambier":(-37.83,140.78),"Gawler":(-34.60,138.74),"Goulburn":(-34.75,149.72),
"Hawkesbury":(-33.61,150.75),"Gosford":(-33.42,151.34),"Newcastle":(-32.93,151.78),"Scone":(-32.05,150.87),"Kembla Grange":(-34.47,150.80),"Nowra":(-34.88,150.60),
"Corowa":(-35.99,146.38),"Wangaratta ":(-36.36,146.31),"Lindsay Park":(-34.47,138.90),"Ballan":(-37.60,144.23),"Lara":(-38.02,144.41),"Tyabb":(-38.26,145.19),
"Balnarring":(-38.37,145.13),"Bacchus Marsh":(-37.67,144.44),"Gisborne":(-37.49,144.59),"Romsey":(-37.35,144.74),"Lancefield":(-37.28,144.73),"Nagambie":(-36.79,145.15),
"Shepparton":(-36.38,145.40),"Yarrawonga":(-36.01,146.00),"Beaumaris":(-37.98,145.04),"Mount Macedon":(-37.42,144.59),"Spring Mount":(-37.5,144.5)}
def hav(a,b):
    la1,lo1=np.radians(a); la2,lo2=np.radians(b); d=np.sin((la2-la1)/2)**2+np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2; return 2*6371*np.arcsin(np.sqrt(d))
tl=D["training_location"].astype(str); tk=D["track"][ri].astype(str)
km=np.array([hav(LL[t],LL[k]) if t in LL and k in LL else np.nan for t,k in zip(tl,tk)])
print("travel coverage",np.isfinite(km).mean().round(3)," median km",np.nanmedian(km).round(0))
far=(km>=200).astype(float); home=(km<=40).astype(float)
G=np.column_stack([np.nan_to_num(np.log1p(km),nan=np.nanmedian(np.log1p(km))),np.isfinite(km),far,home,rrel(np.nan_to_num(km,nan=np.nanmedian(km)))])
np.save("G_travel.npy",G)
evaluate(V4,"live (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,G]),"live + travel distance")
