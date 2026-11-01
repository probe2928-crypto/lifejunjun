import numpy as np, subprocess, sys
SR=44100; D=15.0; N=int(SR*D)
def load(p,ss=0,dur=None):
    cmd=['ffmpeg','-v','error','-ss',str(ss),'-i',p]+(['-t',str(dur)] if dur else [])+['-ac','2','-ar',str(SR),'-f','f32le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,np.float32).reshape(-1,2).copy()
mix=np.zeros((N,2),np.float32)
def put(x,t,g):
    i=int(t*SR); j=min(N,i+len(x)); mix[i:j]+=x[:j-i]*g
mus=load('../raspberry_lofi.m4a',40,D); env=np.ones(len(mus)); 
env[:int(.3*SR)]=np.linspace(0,1,int(.3*SR)); env[-int(1.2*SR):]=np.linspace(1,0,int(1.2*SR))
# duck music under siren 9.9-12.3
t=np.arange(len(mus))/SR; duck=np.where((t>9.8)&(t<12.3),0.45,1.0); duck=np.convolve(duck,np.ones(4410)/4410,'same')
put(mus*(env*duck)[:,None],0,0.55)
wh=load('../whoosh.wav'); hit=load('../hit.wav')
for tt in [2.0,4.35,6.6,9.4,12.1]: put(wh,tt,0.6)
for tt in [0.32,3.55,4.95,11.25,12.6]: put(hit,tt,0.8)
# clock ticks 09:04:57..59
for k in range(3):
    n=int(.03*SR); tk=np.sin(2*np.pi*2400*np.arange(n)/SR)*np.exp(-np.arange(n)/(.004*SR)); put(np.stack([tk,tk],1),2.45+0.37*k,0.35)
# synth siren (rising wail) 9.9-12.3
dur=2.4; n=int(dur*SR); tt=np.arange(n)/SR
f=420+260*np.clip(tt/0.8,0,1)  # rise then hold
ph=2*np.pi*np.cumsum(f)/SR; s=(np.sin(ph)+0.35*np.sin(2*ph))*0.5
a=np.minimum(1,tt/0.5)*np.minimum(1,(dur-tt)/0.6)
put(np.stack([s*a,s*a],1),9.9,0.22)
mix=np.tanh(mix*1.1)*0.9
mix.astype(np.float32).tofile('a.f32')
subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','2','-i','a.f32','-c:a','aac','-b:a','192k','tr905_a.m4a'],check=True)
