import numpy as np, subprocess
SR=44100; D=37.3; N=int(SR*D)
def load(p,ss=0,dur=None):
    cmd=['ffmpeg','-v','error','-ss',str(ss),'-i',p]+(['-t',str(dur)] if dur else [])+['-vn','-ac','2','-ar',str(SR),'-f','f32le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,np.float32).reshape(-1,2).copy()
mix=np.zeros((N,2),np.float32); voice=np.zeros(N,np.float32)
def put(x,t,g,env=None):
    i=int(t*SR); j=min(N,i+len(x)); y=x[:j-i]*g
    if env is not None: y=y*env[:j-i,None]
    mix[i:j]+=y
starts=[0.0,4.7,12.9,17.1,23.5,28.7]
files=['tr905m_00','tr905n_00','tr905m_02','tr905m_03','tr905m_04','tr905n_01']
for k,s in enumerate(starts):
    v=load(files[k]+'.mp3'); put(v,s,1.0); i=int(s*SR); voice[i:i+len(v)]=1
# ducking envelope from voice presence
sm=np.convolve(voice,np.ones(int(.25*SR))/int(.25*SR),'same')
mus=load('../../raspberry_lofi.m4a',55,D)[:N]; n=len(mus)
duck=(1-0.72*sm[:n]); t=np.arange(n)/SR
duck*=np.where((t>4.6)&(t<9.3),0.35,1.0)*np.where((t>9.3)&(t<12.85),0.0,1.0)    # make room for the real siren
fade=np.clip(t/0.4,0,1)*np.clip((D-t)/1.5,0,1)
put(mus,0,0.5,duck*fade)
SD=12.85; sir=load('siren905_53032875.webm',0,SD); ts=np.arange(len(sir))/SR
senv=np.where(ts<4.65,0.16,np.where(ts<9.3,0.30,1.0))*np.clip(ts/0.2,0,1)*np.clip((SD-ts)/0.5,0,1)
senv=np.convolve(senv,np.ones(4410)/4410,'same')
put(sir,0,2.6,senv)
wh=load('../../whoosh.wav'); hit=load('../../hit.wav')
for tt in [4.45,12.7,16.85,23.15,28.35]: put(wh,tt,0.5)
for tt in [3.3,8.1,15.25,18.38,29.72]: put(hit,tt,0.7)
for k in range(3):
    m=int(.03*SR); tk=np.sin(2*np.pi*2400*np.arange(m)/SR)*np.exp(-np.arange(m)/(.004*SR)); put(np.stack([tk,tk],1),14.14+0.37*k,0.3)
pk=np.abs(mix).max(); mix=np.tanh(mix/pk*1.4)*0.92
mix.astype(np.float32).tofile('a.f32')
subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','2','-i','a.f32','-af','loudnorm=I=-14:TP=-1.5','-ar','44100','-c:a','aac','-b:a','192k','tr905n_a.m4a'],check=True)
