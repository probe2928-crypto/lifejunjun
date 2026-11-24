import numpy as np, subprocess
SR=44100; D=17.2; N=int(SR*D)
def load(p,ss=0,dur=None):
    cmd=['ffmpeg','-v','error','-ss',str(ss),'-i',p]+(['-t',str(dur)] if dur else [])+['-vn','-ac','2','-ar',str(SR),'-f','f32le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,np.float32).reshape(-1,2).copy()
mix=np.zeros((N,2),np.float32); voice=np.zeros(N,np.float32)
def put(x,t,g,env=None):
    i=int(t*SR); j=min(N,i+len(x)); y=x[:j-i]*g
    if env is not None: y=y*env[:j-i,None]
    mix[i:j]+=y
for k,s in enumerate([0.15,2.48,7.9,10.83,13.9]):
    v=load(f'../vo_0{k}.wav'); put(v,s,1.0); i=int(s*SR); voice[i:i+len(v)]=1
sm=np.convolve(voice,np.ones(int(.25*SR))/int(.25*SR),'same')
mus=load('../../raspberry_lofi.m4a',95,D)[:N]; n=len(mus); t=np.arange(n)/SR
put(mus,0,0.45,(1-0.72*sm[:n])*np.clip(t/0.3,0,1)*np.clip((D-t)/1.2,0,1))
wh=load('../../whoosh.wav'); hit=load('../../hit.wav')
for tt in [2.3,7.6,10.55,13.6]: put(wh,tt,0.4)
for tt in [0.3,5.9,11.8,14.9]: put(hit,tt,0.55)
pk=np.abs(mix).max(); mix=np.tanh(mix/pk*1.3)*0.9
mix.astype(np.float32).tofile('a.f32')
subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','2','-i','a.f32','-af','loudnorm=I=-14:TP=-1.5,alimiter=limit=0.84:level=false','-ar','44100','-c:a','aac','-b:a','192k','a.m4a'],check=True)
