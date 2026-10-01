"""First starters on a day export as ["race|horse", ...]. python fs_json.py UP_NPZ OUT_JSON"""
import numpy as np, json, sys
U=np.load(sys.argv[1],allow_pickle=True); cols=list(U["cols"]); ri=U["race_idx"]; f=U["X"][:,cols.index("firstStarter")]
json.dump([f"{int(U['race_number'][ri[k]])}|{U['name'][k]}" for k in range(len(ri)) if f[k]==1],open(sys.argv[2],"w")); print("first starters:",int(np.nansum(f==1)))
