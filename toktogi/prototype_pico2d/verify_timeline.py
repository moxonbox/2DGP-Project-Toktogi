"""Pure-clock backlog and stable-order contract."""
from timeline import FixedStepTimeline

def verify():
    line=FixedStepTimeline(1/120)
    applied=[]; ticks=[]
    line.push('first',.05); line.push('second',.05)
    line.advance(3,applied.append,lambda dt,on_input:(ticks.append(dt),on_input()),lambda e:'tick')
    assert len(ticks)==240 and line.overload and applied==['first','second']
    line.advance(0,applied.append,lambda dt,on_input:(ticks.append(dt),on_input()),lambda e:'tick')
    assert len(ticks)==360 and not line.overload
    assert abs(sum(ticks)-3)<1e-10
    for bad in (-1,float('nan'),float('inf')):
        try: line.advance(bad,None,None,None)
        except ValueError: pass
        else: raise AssertionError(bad)
    return {'ticks':360,'backlog_preserved':True,'equal_time_order':True}

if __name__=='__main__': print(verify())
