"""Timestamp-ordered input and fixed-step simulation, independent of SDL."""
import heapq
from math import isfinite


class FixedStepTimeline:
    def __init__(self, step, max_ticks=240):
        if not isfinite(step) or step<=0:
            raise ValueError('Fixed step must be finite and positive.')
        if type(max_ticks) is not int or max_ticks<1:
            raise ValueError('max_ticks must be a positive integer.')
        self.step = step
        self.max_ticks = max_ticks
        self.pending = []
        self.event_sequence = 0
        self.wall_time = self.tick_wall = self.accumulator = 0.
        self.overload = False

    def push(self, event, at):
        if not isfinite(at):
            raise ValueError('Input time must be finite.')
        self.event_sequence += 1
        heapq.heappush(self.pending, (max(self.tick_wall, at), self.event_sequence, event))

    def drain(self, until):
        while self.pending and self.pending[0][0] <= until+1e-9:
            yield heapq.heappop(self.pending)[2]

    def advance(self, dt, dispatch, tick, route):
        if not isfinite(dt) or dt < 0:
            raise ValueError('Frame time must be finite and nonnegative.')
        self.wall_time += dt
        self.accumulator += dt
        for _ in range(self.max_ticks):
            for event in self.drain(self.tick_wall):
                dispatch(event)
            if self.accumulator < self.step-1e-9:
                break
            due = list(self.drain(self.tick_wall+self.step))
            remaining = due

            def apply_input():
                nonlocal remaining
                remaining = []
                closed = False
                for event in due:
                    phase = route(event)
                    if phase == 'tick' and not closed:
                        dispatch(event)
                    else:
                        remaining.append(event)
                        closed |= phase == 'close'

            tick(self.step, apply_input)
            for event in remaining:
                dispatch(event)
            self.tick_wall += self.step
            self.accumulator = max(0., self.accumulator-self.step)
        self.overload = self.accumulator >= self.step
        for event in self.drain(self.tick_wall):
            dispatch(event)
