"""network variants on the lab split: python nnx.py ARCH ; appends xp.log"""
import numpy as np, torch, bench as b, lab, nn, sys, time
torch.set_num_threads(int(sys.argv[2]) if len(sys.argv)>2 else 2)
arch=sys.argv[1]
class SetNet(torch.nn.Module):
    """each runner sees the field: runner encoding + (encoding - field mean) + field max, then a scorer"""
    def __init__(s,k,h=128,drop=0.2):
        super().__init__()
        s.enc=torch.nn.Sequential(torch.nn.Linear(k,h),torch.nn.ReLU(),torch.nn.Dropout(drop))
        s.head=torch.nn.Sequential(torch.nn.Linear(3*h,64),torch.nn.ReLU(),torch.nn.Dropout(drop),torch.nn.Linear(64,1))
    def forward(s,x,m):
        e=s.enc(x); mf=m.unsqueeze(-1).float()
        mean=(e*mf).sum(1,keepdim=True)/mf.sum(1,keepdim=True).clamp_min(1)
        mx=e.masked_fill(~m.unsqueeze(-1),-1e4).max(1,keepdim=True).values
        z=s.head(torch.cat([e,e-mean,mx.expand_as(e)],-1)).squeeze(-1)
        return torch.log_softmax(z.masked_fill(~m,-1e9),-1)
class AttnNet(torch.nn.Module):
    """one self-attention layer over the runners"""
    def __init__(s,k,h=128,drop=0.2):
        super().__init__()
        s.enc=torch.nn.Sequential(torch.nn.Linear(k,h),torch.nn.ReLU(),torch.nn.Dropout(drop))
        s.att=torch.nn.MultiheadAttention(h,4,dropout=drop,batch_first=True); s.ln=torch.nn.LayerNorm(h)
        s.head=torch.nn.Sequential(torch.nn.Linear(h,64),torch.nn.ReLU(),torch.nn.Dropout(drop),torch.nn.Linear(64,1))
    def forward(s,x,m):
        e=s.enc(x); a,_=s.att(e,e,e,key_padding_mask=~m); e=s.ln(e+a)
        z=s.head(e).squeeze(-1); return torch.log_softmax(z.masked_fill(~m,-1e9),-1)
kw={}
if arch=="set": nn.Net=SetNet
elif arch=="attn": nn.Net=AttnNet
elif arch=="wide": kw=dict(h=256)
elif arch=="drop3": kw=dict(drop=0.3)
F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n")
t0=time.time(); p,ep=nn.fit(F,names,lab.INNER,lab.VALID,epochs=80,seed=0,**kw); np.save(f"valid_nn_{arch}.npy",p)
open("xp.log","a").write(b.fmt(f"net {arch} ep{ep}",b.score(p,lab.VALID))+f" {time.time()-t0:.0f}s\n")
