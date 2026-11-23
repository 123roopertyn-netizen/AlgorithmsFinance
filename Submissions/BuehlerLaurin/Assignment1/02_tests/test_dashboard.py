"""Saved-file analysis gates and Streamlit's real application smoke test."""
import math
from pathlib import Path
import sys

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '04_dashboard'))
import saved_results as saved

TABS = ['Overview', 'Scaling', 'Original vs revised & variants',
        'Throughput & latency', 'Memory', 'Correctness',
        'Bottleneck explained', 'Method & data']


@pytest.fixture(scope='module')
def bundle():
    return saved.load_bundle(saved.head())


def test_official_headlines_match_committed_csvs(bundle):
    got = saved.official_geomeans(bundle).set_index('version')
    for version, role in [('B1','candidates'),('B2','candidates'),('B3','candidates'),('B3r','baseline')]:
        rows = bundle['tables'][role]['summary']
        rows = rows[(rows.version == version) & (rows.experiment == 'official')
                    & (rows['size'] == 100000) & (rows.phase == 'replay')]
        assert len(rows) == 15 and set(rows.status) == {'ok'}
        expected = math.exp(math.fsum(math.log(v) for v in rows.median_s) / 15)
        assert got.loc[version, 'geomean_s'] == pytest.approx(expected, rel=1e-12)
        assert got.loc[version, 'cells'] == 15


def test_stopped_a_is_bound_only_not_a_time(bundle):
    limits = saved.replay_limits(bundle)
    raw = bundle['tables']['baseline']['stops']
    expected = raw[(raw.version == 'A') & (raw.phase == 'replay')
                   & (raw.reason == 'phase_time_limit')].case_id.nunique()
    assert len(limits) == expected == 13
    assert set(limits.bound_s) == {600}
    assert limits.time_label.str.startswith('> 600 s').all()


@pytest.mark.parametrize('fault', ['duplicate', 'missing', 'nan', 'stopped', 'not_run'])
def test_bad_cells_never_enter_medians(fault):
    summary = pd.DataFrame([dict(case_id='x', version='A', phase='replay', status='ok',
        median_s=3., completed_repeats=5, repeats_requested=5)])
    timing = pd.DataFrame([dict(case_id='x', version='A', phase='replay', status='ok',
        repeat=i, seconds=i+1., warmup=False) for i in range(5)])
    cells = pd.DataFrame([dict(case_id='x', version='A', mode='timing', status='ok')])
    if fault == 'duplicate': timing = pd.concat([timing, timing.iloc[:1]], ignore_index=True)
    if fault == 'missing': timing = timing.iloc[:4]
    if fault == 'nan': timing.loc[0,'seconds'] = float('nan')
    if fault in ('stopped','not_run'): cells.loc[0,'status'] = fault
    got = saved.validate_summary(summary, timing, cells).iloc[0]
    assert not got.complete and pd.isna(got.median_s)


def test_fit_uses_measured_points_only():
    rows = pd.DataFrame([dict(version='A', size=n, median_s=n*n, complete=True)
                         for n in (10,100,1000)] +
                        [dict(version='A', size=10000, median_s=float('nan'), complete=False)])
    fit = saved.fit_exponents(rows).iloc[0]
    assert fit.exponent == pytest.approx(2.) and fit.points == 3
    assert fit.min_size == 10 and fit.max_size == 1000


def test_loader_restricts_paths_and_uses_a_fixed_commit(bundle):
    store = bundle['store']
    assert len(store.revision) == 40
    with pytest.raises(ValueError): store.text('01_code/lob/book_a.py')
    with pytest.raises(ValueError): store.text('03_results/runs/../../README.md')
    assert store.text('05_evidence/not_a_committed_evidence_file.txt') is None
    assert 'Final Version B: B3r' in bundle['selection']


def test_regression_long_committed_git_blob_path(bundle):
    assert bundle['rematch']['decision'] == 'rejected'
    assert bundle['rematch']['scenario_losses'][0]['workload'] == 'dead_slot_rebuild'
    assert bundle['rematch']['official_100k_ratio'] == pytest.approx(.8731749844948045)


def test_b1_counter_example_is_measured(bundle):
    shown = saved.observations(bundle,'counts',candidate_versions=('B1',))
    shown = shown[shown.version.eq('B1') & shown.workload.eq('far_end_flicker') & shown.counter.eq('price_list_shifts')]
    raw = bundle['tables']['baseline']['counts']
    raw = raw[raw.version.eq('B1') & raw.workload.eq('far_end_flicker') & raw.counter.eq('price_list_shifts')]
    assert len(shown) == len(raw) > 0
    assert shown.value.tolist() == raw.value.tolist()


def test_all_eight_tabs_render_and_headlines_match_csv(bundle,monkeypatch):
    import socket
    local_connect = socket.socket.connect
    def no_external_network(sock,address):
        # Windows asyncio builds its internal socketpair using loopback TCP.
        if sock.family == getattr(socket,'AF_UNIX',None) or address[0] in ('127.0.0.1','::1'):
            return local_connect(sock,address)
        raise AssertionError('dashboard attempted an external network connection')
    monkeypatch.setattr(socket.socket,'connect',no_external_network)
    app = AppTest.from_file(str(ROOT / '04_dashboard/app.py'), default_timeout=120).run()
    assert not app.exception, [e.message for e in app.exception]
    assert [t.label for t in app.tabs] == TABS
    for tab in app.tabs:
        assert len(tab.dataframe) + len(tab.markdown) + len(tab.metric) > 0, tab.label
    metrics = {m.label:m.value for m in app.metric}
    geo = saved.official_geomeans(bundle).set_index('version').loc['B3r','geomean_s']
    assert metrics['B3r official 100k geomean'] == f'{geo:.4f} s'
    assert metrics['A replay limits'] == str(len(saved.replay_limits(bundle)))
    assert any('cancel_churn' in m.value and 'A is faster' in m.value for m in app.markdown)


def test_fast_rematch_score_is_from_same_session_csv(bundle):
    raw = bundle['tables']['rematch']['summary']
    raw = raw[raw.phase.eq('replay') & raw.experiment.eq('official') & raw['size'].eq(100000)]
    times = raw.pivot(index='case_id',columns='version',values='median_s')
    assert len(times) == 15
    ratio = math.exp(sum(math.log(v) for v in times.B3r_fast / times.B3r) / len(times))
    assert ratio == pytest.approx(bundle['rematch']['official_100k_ratio'],rel=1e-12)


def test_histogram_is_a_distribution_not_rebuilt_from_percentiles(bundle):
    h = saved.observations(bundle,'latency_histogram')
    q = saved.observations(bundle,'latency')
    case = 'official_buildup_1000_s42_l1000'
    h = h[h.case_id.eq(case) & h.event_type.eq('ALL') & h.segment.eq('all')]
    q = q[q.case_id.eq(case) & q.event_type.eq('ALL') & q.segment.eq('all')]
    totals = h.groupby('version')['count'].sum()
    pd.testing.assert_series_equal(totals.sort_index(),q.set_index('version').n.sort_index(),check_names=False)
    assert len(h) > 4


def test_dashboard_interactive_views_render(bundle):
    app = AppTest.from_file(str(ROOT / '04_dashboard/app.py'),default_timeout=120).run()
    app.selectbox(key='scale_phase').select('construction')
    app.radio(key='liq_phase').set_value('replay')
    app.selectbox(key='variant_part').select('post_attack')
    app.selectbox(key='mem_workload').select('cancel_churn_memory')
    app.run()
    assert not app.exception, [e.message for e in app.exception]
    app.selectbox(key='lat_case').select('official_buildup_10000_s42_l1000')
    app.run()
    app.selectbox(key='lat_segment').select('early')
    app.run()
    assert not app.exception, [e.message for e in app.exception]


def test_subprocess_timeouts_do_not_create_replay_bounds(bundle):
    raw = bundle['tables']['baseline']['stops'].copy()
    raw['reason'] = 'subprocess_wall_time_limit'
    fake = {'tables':{'baseline':{'stops':raw}}}
    assert saved.replay_limits(fake).empty
