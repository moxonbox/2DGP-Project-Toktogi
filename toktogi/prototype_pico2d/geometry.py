"""Logical top-left rectangles shared by Pillow drawing and input hit tests."""
from dataclasses import dataclass

@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int
    def __iter__(self): return iter((self.x,self.y,self.w,self.h))
    @property
    def size(self): return self.w,self.h
    @property
    def width(self): return self.w
    @property
    def height(self): return self.h
    @property
    def left(self): return self.x
    @property
    def top(self): return self.y
    @property
    def right(self): return self.x+self.w
    @property
    def bottom(self): return self.y+self.h
    @property
    def topleft(self): return self.x,self.y
    @property
    def center(self): return self.x+self.w//2,self.y+self.h//2
    @center.setter
    def center(self,point): self.x,self.y=point[0]-self.w//2,point[1]-self.h//2
    @property
    def centerx(self): return self.center[0]
    @property
    def centery(self): return self.center[1]
    def collidepoint(self,point): return self.left<=point[0]<self.right and self.top<=point[1]<self.bottom
    def inflate(self,x,y): return Rect(self.x-x//2,self.y-y//2,self.w+x,self.h+y)

def crop_box(rect):
    x,y,w,h=rect
    return round(x),round(y),round(x+w),round(y+h)

def bounds(rect):
    x,y,right,bottom=crop_box(rect)
    return x,y,max(x,right-1),max(y,bottom-1)

def circle_bounds(point,radius):
    x,y=point
    return x-radius,y-radius,x+radius,y+radius
