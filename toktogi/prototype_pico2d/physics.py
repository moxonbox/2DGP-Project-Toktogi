"""Pure Capsule sweeps and overlap tests. Coordinates use screen Y down."""

STEP = 1/120
GRAVITY = 850
CAP_RADIUS = 14
CAP_HEIGHT = 52

def approach(value, goal, amount):
    return min(value+amount,goal) if value<goal else max(value-amount,goal)


def overhang(distance):
    return (CAP_RADIUS**2-distance**2)**.5 if distance<CAP_RADIUS else 0.


def capsule_overlaps(platform,x,y):
    horizontal=max(platform.x0-x,x-platform.x1,0.)
    vertical=max(platform.y-(y-CAP_RADIUS),(y-CAP_HEIGHT+CAP_RADIUS)-platform.bottom,0.)
    return horizontal*horizontal+vertical*vertical<CAP_RADIUS**2-1e-9


def segment_box(a,b,box,*,include_end=True):
    lo,hi=0.,1.
    for p,q,mn,mx in zip(a,b,box[:2],box[2:]):
        delta=q-p
        if abs(delta)<1e-10:
            if not mn<=p<=mx:return False
        else:
            t0,t1=sorted(((mn-p)/delta,(mx-p)/delta))
            lo,hi=max(lo,t0),min(hi,t1)
            if lo>hi:return False
    return include_end or lo<1.


def sweep_x(platforms,x,y,vx,dt):
    nx=x+vx*dt
    end=nx
    # Horizontal sweep of the two capsule caps and the straight segment.
    for platform in platforms:
        if abs(y-platform.y)<1e-8:
            continue
        distance=max(0.,platform.y-(y-CAP_RADIUS),(y-CAP_HEIGHT+CAP_RADIUS)-platform.bottom)
        radius=overhang(distance)
        if not radius:
            continue
        left,right=platform.x0-radius,platform.x1+radius
        if vx>0 and x<=left<nx:
            nx=left
        elif vx<0 and nx<right<=x:
            nx=right
    return nx,0. if nx!=end else vx


def sweep_y(platforms,x,y,vy,dt):
    vy=min(660.,vy+GRAVITY*dt)
    bottom=y+vy*dt
    contact=None
    for platform in platforms:
        distance=max(platform.x0-x,x-platform.x1,0.)
        radius=overhang(distance)
        if not radius:
            continue
        if vy>=0:
            surface=platform.y+CAP_RADIUS-radius
            if y<=surface<=bottom:
                contact=platform
                bottom=surface
        else:
            ceiling=platform.bottom+CAP_HEIGHT-CAP_RADIUS+radius
            if bottom<=ceiling<=y:
                bottom=ceiling
                contact=platform
    return bottom,vy,contact
