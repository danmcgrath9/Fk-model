exec(open("t_s2feat.py").read().split("evaluate(base,")[0])
def enc(key,k=10):
    s={};n={};out=np.zeros(len(ri))
    for ix in byd:
        for i in ix:
            if key[i] in s: out[i]=s[key[i]]/(n[key[i]]+k)
        for i in ix: s[key[i]]=s.get(key[i],0)+res[i]; n[key[i]]=n.get(key[i],0)+1
    return out
st=np.nan_to_num(F7[:,c["f_careerForm_s"]],nan=0); fsf=np.where(st<1,"FS","R")
S=D["sire"].astype(str); DS=D["dam_sire"].astype(str)
Eb=np.column_stack([enc(np.char.add(tr,fsf),5),enc(np.char.add(S,fsf),10),enc(DS,20)])
Eb=np.column_stack([Eb,np.stack([cen(Eb[:,j]) for j in range(3)],1)])
X1=np.column_stack([base,A,Bk,C]); np.save("s2_extra.npy",np.column_stack([A,Bk,C]))
evaluate(np.column_stack([X1,Eb]),"+ trainer/sire first-starter, dam-sire gaps")
