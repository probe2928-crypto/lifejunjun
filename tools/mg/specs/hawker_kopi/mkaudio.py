import numpy as np, subprocess, json
SR=44100; D=20.3; N=int(SR*D)
def load(p,ss=0,dur=None):
    cmd=['ffmpeg','-v','error','-ss',str(ss),'-i',p]+(['-t',str(dur)] if dur else [])+['-vn','-ac','2','-ar',str(SR),'-f','f32le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,np.float32).reshape(-1,2).copy()
mix=np.zeros((N,2),np.float32); voice=np.zeros(N,np.float32)
def put(x,t,g,env=None):
    i=int(t*SR); j=min(N,i+len(x)); y=x[:j-i]*g
    if env is not None: y=y*env[:j-i,None]
    mix[i:j]+=y
starts=json.load(open('../vo.json'))['starts']
for k,s in enumerate(starts):
    v=load(f'../vo_0{k}.mp3'); put(v,s,1.0); i=int(s*SR); voice[i:i+len(v)]=1
sm=np.convolve(voice,np.ones(int(.25*SR))/int(.25*SR),'same')
mus=load('../../raspberry_lofi.m4a',70,D)[:N]; n=len(mus); t=np.arange(n)/SR
duck=(1-0.7*sm[:n]); fade=np.clip(t/0.3,0,1)*np.clip((D-t)/1.5,0,1)
put(mus,0,0.5,duck*fade)
wh=load('../../whoosh.wav'); hit=load('../../hit.wav')
for tt in [5.45,8.0,10.85,14.0]: put(wh,tt,0.45)
for tt in [0.9,3.1,6.9,11.6,13.5,16.8,17.6]: put(hit,tt,0.6)
# ice clinks at 13.5
for k in range(3):
    m=int(.06*SR); tk=np.sin(2*np.pi*3200*np.arange(m)/SR)*np.exp(-np.arange(m)/(.012*SR)); put(np.stack([tk,tk],1),13.6+0.07*k,0.25)
pk=np.abs(mix).max(); mix=np.tanh(mix/pk*1.4)*0.92
mix.astype(np.float32).tofile('a.f32')
subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','2','-i','a.f32','-af','loudnorm=I=-14:TP=-1.5,alimiter=limit=0.84:level=false','-ar','44100','-c:a','aac','-b:a','192k','a.m4a'],check=True)
