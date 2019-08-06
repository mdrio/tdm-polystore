import pytest
import json
from tdmq.client.client import Client
import numpy as np
from datetime import datetime, timedelta


def register_sources(c, N=None):
    with open('../data/sources.json') as f:
        descs = json.load(f)['sources']
    descs = [d for d in descs if 'shape' in d and len(d['shape']) > 0]
    srcs = []
    for d in descs:
        if N is None:
            s = c.register_source(d)
        else:
            s = c.register_source(d, N)
        check_source(s, d)
        srcs.append(s)
    return srcs


def create_data_frame(shape, properties, slot):
    data = {}
    for p in properties:
        data[p] = np.full(shape, slot, dtype=np.float32)
    return data


def ingest_records(s, N):
    now = datetime.now()
    t = now
    dt = timedelta(seconds=10)
    for slot in range(N):
        data = create_data_frame(s.shape, s.controlled_properties, slot)
        s.ingest(t, data, slot)
        t += dt
    return now, dt


def check_records(s, timebase, dt, N):
    ts = s.timeseries()
    ts_times, D = ts[:]
    t = timebase
    for p in s.controlled_properties:
        assert D[p].shape == (N,) + s.shape
    for i in range(N):
        assert (ts_times[i] - t).total_seconds() < 1.0e-5
        t += dt
        for p in s.controlled_properties:
            assert D[p][i].min() == D[p][i].max()
            assert int(D[p][i].min()) == i


def check_source(s, d):
    for k in ['entity_category', 'entity_type']:
        assert getattr(s, k) == d[k]
    assert s.shape == tuple(d['shape'])
    assert s.controlled_properties == d['controlledProperties']
    sdf = s.default_footprint
    ddf = d['default_footprint']
    assert sdf['type'] == ddf['type']
    assert np.allclose(sdf['coordinates'], ddf['coordinates'])


def check_deallocation(c, tdmq_ids):
    sources = dict((_.tdmq_id, _) for _ in c.get_sources())
    for tid in tdmq_ids:
        assert tid not in sources


def test_nonscalar_source_register_deregister():
    c = Client()
    srcs = register_sources(c)
    sources = dict((_.tdmq_id, _) for _ in c.get_sources())
    tdmq_ids = []
    for s in srcs:
        assert s.tdmq_id in sources
        assert s.id == sources[s.tdmq_id].id
        assert s.tdmq_id == sources[s.tdmq_id].tdmq_id
        assert s.tdmq_id in c.managed_objects
        assert s == c.managed_objects[s.tdmq_id]
        assert s == sources[s.tdmq_id]
        tdmq_id = s.tdmq_id
        c.deregister_source(s)
        tdmq_ids.append(tdmq_id)
    check_deallocation(c, tdmq_ids)


def test_nonscalar_source_add_records():
    N = 10
    c = Client()
    srcs = register_sources(c, N)
    tdmq_ids = []
    for s in srcs:
        assert len(s.shape) > 0
        timebase, dt = ingest_records(s, N)
        check_records(s, timebase, dt, N)
        tdmq_id = s.tdmq_id
        c.deregister_source(s)
        tdmq_ids.append(tdmq_id)
    check_deallocation(c, tdmq_ids)