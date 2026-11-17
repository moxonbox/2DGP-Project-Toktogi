"""One continuous camera for both levels, stepped with simulation time."""
from physics import approach

class Camera:
    def __init__(self,world):
        self.world=world;self.x=self.y=0.;self.epoch=None
    def step(self,game,dt):
        if self.world.legacy:self.x=self.y=0.;return
        if game.run!='Playing':return
        left,top,right,bottom=self.world.camera_bounds
        target_x=min(game.x-240,max(game.x-720,self.x))
        target_y=min(game.y-140,max(game.y-400,self.y))
        target_x=max(left,min(right-960,target_x))
        target_y=max(top,min(bottom-560,target_y))
        if self.epoch!=self.world.run_epoch:
            self.x,self.y=target_x,target_y;self.epoch=self.world.run_epoch
        else:
            self.x=approach(self.x,target_x,480*dt)
            self.y=approach(self.y,target_y,480*dt)
    def point(self,x,y):return round(x-self.x),round(y-self.y)

def verify():
    from world import World
    from types import SimpleNamespace
    w=World.seamless();c=Camera(w);g=SimpleNamespace(x=990.,y=125.,run='Playing')
    c.step(g,1/120);before=(c.x,c.y)
    g.x=1010;c.step(g,1/120)
    assert abs(c.x-before[0])<=4 and abs(c.y-before[1])<=4
    g.run='Paused';before=(c.x,c.y);g.x=1800;c.step(g,1)
    assert before==(c.x,c.y)
    c.x=.6;c.y=.4;assert c.point(1.4,1.2)==(1,1)
    return {'continuous_boundary':True,'paused_camera':True,'single_rounding':True}
