import json, sys, html
from build_calc import data
title,model,prices,out,key,sub=sys.argv[1:7]
sb=json.load(open(sys.argv[7])) if len(sys.argv)>7 and sys.argv[7]!='-' else []
ang=json.load(open(sys.argv[8])) if len(sys.argv)>8 else {}
fs=json.load(open(sys.argv[9])) if len(sys.argv)>9 else []
open(out,"w").write(open("market_tpl.html").read().replace("__TITLE__",html.escape(title)).replace("__SUB__",html.escape(sub)).replace("__KEY__",key).replace("__DATA__",json.dumps(data(model,prices,sb,ang,fs))))
print("ok",out)
