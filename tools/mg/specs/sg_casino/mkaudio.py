import numpy as np, subprocess, wave
SR=44100; DUR=28.3; N=int(SR*DUR)
def load(p):
    b=subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(b,np.float32)
vo=np.zeros(N,np.float32)
for i,t in enumerate([0.15,3.95,10.85,16.0,23.5]):
    v=load(f'../vo_0{i}.wav'); s=int(t*SR); vo[s:s+len(v)]+=v[:N-s]
# soft pad: Am - F - C - G, 2.2s each, warm sines + slow tremolo
t=np.arange(N)/SR; bed=np.zeros(N)
ch=[[220,261.6,329.6],[174.6,220,261.6],[196,261.6,329.6],[196,246.9,293.7]]
L=3.35
for k in range(int(DUR/L)+1):
    s=int(k*L*SR); e=min(N,int((k+1)*L*SR)+int(.3*SR)); n=e-s
    if n<=0: break
    tt=np.arange(n)/SR; env=np.minimum(1,tt/.35)*np.minimum(1,(n/SR-tt)/.5)
    for f in ch[k%4]:
        bed[s:e]+=env*(np.sin(2*np.pi*f*tt)+.3*np.sin(2*np.pi*2*f*tt))/3
    # soft kick-ish pulse every beat (0.42s)
for b in np.arange(0,DUR,0.8375):
    s=int(b*SR); n=int(.18*SR); tt=np.arange(n)/SR
    if s+n<N: bed[s:s+n]+=np.sin(2*np.pi*(60+60*np.exp(-tt*30))*tt)*np.exp(-tt*18)*.9
# whoosh at cuts
rng=np.random.default_rng(1)
for c in [3.85,10.75,15.95,23.15]:
    n=int(.5*SR); s=int((c-.35)*SR); w=rng.standard_normal(n); 
    w=np.convolve(w,np.ones(30)/30,'same'); env=np.sin(np.pi*np.arange(n)/n)**2
    bed[s:s+n]+=w*env*1.2
bed*=0.12/np.abs(bed).max()
# duck under voice
env=np.convolve(np.abs(vo),np.ones(int(.08*SR))/int(.08*SR),'same'); duck=1-.45*np.clip(env*8,0,1)
mix=vo*0.95+bed*duck
fade=np.ones(N); fn=int(.8*SR); fade[-fn:]=np.linspace(1,0,fn); mix*=fade
mix*=10**(2/20); mix/=max(1,np.abs(mix).max()/0.95)
st=np.stack([mix,mix],1)
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-','-c:a','aac','-b:a','192k','mix.m4a'],input=st.astype(np.float32).tobytes())
print('ok')
