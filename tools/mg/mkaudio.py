import numpy as np, subprocess, sys
SR=44100; D=float(sys.argv[1]); N=int(SR*D); pref=sys.argv[2]; starts=[float(x) for x in sys.argv[3].split(',')]
wh_t=[float(x) for x in sys.argv[4].split(',')]; hit_t=[float(x) for x in sys.argv[5].split(',')]; out=sys.argv[6]; mss=float(sys.argv[7]) if len(sys.argv)>7 else 30
def load(p,ss=0,dur=None):
    cmd=['ffmpeg','-v','error','-ss',str(ss),'-i',p]+(['-t',str(dur)] if dur else [])+['-vn','-ac','2','-ar',str(SR),'-f','f32le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,np.float32).reshape(-1,2).copy()
mix=np.zeros((N,2),np.float32); voice=np.zeros(N,np.float32)
def put(x,t,g,env=None):
    i=int(t*SR); j=min(N,i+len(x)); y=x[:j-i]*g
    if env is not None: y=y*env[:j-i,None]
    mix[i:j]+=y
for k,s in enumerate(starts):
    v=load(f'{pref}_{k:02d}.mp3'); put(v,s,1.0); i=int(s*SR); voice[i:i+len(v)]=1
sm=np.convolve(voice,np.ones(int(.25*SR))/int(.25*SR),'same')
mus=load('/home/claude/r3/raspberry_lofi.m4a',mss,D)[:N]; n=len(mus); t=np.arange(n)/SR
fade=np.clip(t/0.3,0,1)*np.clip((D-t)/1.2,0,1)
put(mus,0,0.5,(1-0.72*sm[:n])*fade)
wh=load('/home/claude/r3/whoosh.wav'); hit=load('/home/claude/r3/hit.wav')
for tt in wh_t: put(wh,tt,0.45)
for tt in hit_t: put(hit,tt,0.6)
pk=np.abs(mix).max(); mix=np.tanh(mix/pk*1.4)*0.92
mix.astype(np.float32).tofile('/tmp/a.f32')
subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','2','-i','/tmp/a.f32','-af','loudnorm=I=-14:TP=-1.5','-ar','44100','-c:a','aac','-b:a','192k',out],check=True)
