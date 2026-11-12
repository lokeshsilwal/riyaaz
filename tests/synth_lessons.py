"""Synthetic singers for the Learn-tab lessons, each with a known fault (or none).

Writes cases_lessons/<name>/{audio.f32, meta.json}. meta holds the lesson id, when the
lesson starts in the audio, Sa, and what the app's feedback is expected to say.
Run: python3 synth_lessons.py && python3 evaluate_lessons.py
"""
import json, os
import numpy as np
from scipy.signal import butter, sosfilt
from synth import SR, VOWELS, formant_gain, pink, note_hz, step_cents, rms

HERE = os.path.dirname(os.path.abspath(__file__))
LEAD = 1.5   # seconds of room noise before the lesson starts (the app's count-in)

def path_cents(path, t):
    """Same path rules as the app: [step, dur, glide]."""
    out = np.full(len(t), np.nan); t0 = 0; prev = None
    for p in path:
        c = None if p[0] is None else step_cents(p[0])
        m = (t >= t0) & (t < t0 + p[1])
        if c is not None:
            if len(p) > 2 and p[2] and prev is not None:
                out[m] = prev + (c - prev) * (t[m] - t0) / p[1]
            else:
                out[m] = c
            prev = c
        t0 += p[1]
    return out, t0

def voice(cents, amp, sa, vowel, rng, trill=False):
    """Additive formant voice following a per-sample cents track (nan = silent)."""
    n = len(cents)
    c = np.where(np.isnan(cents), np.nan, cents)
    # fill silent stretches with neighbouring pitch so phase stays continuous
    idx = np.where(~np.isnan(c), np.arange(n), 0); np.maximum.accumulate(idx, out=idx)
    cf = c[idx]; cf[np.isnan(cf)] = np.nanmean(c)
    f0 = sa * 2 ** (cf / 1200)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    sig = np.zeros(n)
    vname = 'oo' if vowel in ('mm', 'trill') else vowel
    for k in range(1, int(5000 / f0.min()) + 1):
        fk = k * f0
        g = formant_gain(fk, vname) * (fk < 6000)
        if vowel == 'mm':
            g = g / (1 + (fk / 400) ** 2)  # hum: closed lips, mostly low harmonics
        sig += g * k ** -1.2 * np.sin(k * phase)
    on = ~np.isnan(cents)
    a = amp * on
    k = np.hanning(int(0.03 * SR)); k /= k.sum()
    a = np.convolve(a, k, mode='same')
    if trill:
        t = np.arange(n) / SR
        a = a * (0.25 + 0.75 * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t)) ** 2)
    sig *= a
    sig += sosfilt(butter(2, 2500, 'hp', fs=SR, output='sos'), rng.normal(0, 1, n)) * a * 0.015
    return sig

def phone(x, rng, snr, ref):
    """Phone mic: room noise at `snr` dB below the voice, low-cut at 200 Hz."""
    p = pink(len(x), rng); x = x + p / rms(p) * ref * 10 ** (-snr / 20)
    x = sosfilt(butter(2, 200, 'hp', fs=SR, output='sos'), x)
    return x / np.max(np.abs(x)) * 0.6

def sing_lesson(lesson_path, sa, rng, lag=0.2, offset=0.0, note_offsets=None, vowel='aa', trill=False,
                loud_top_db=0.0, dyn=None, drift_with_loud=0.0, gaps=(), vib=8, tail=1.0):
    dur_extra = LEAD + tail
    _, pdur = path_cents(lesson_path, np.array([0.0]))
    n = int((pdur + dur_extra) * SR)
    t = np.arange(n) / SR - LEAD                    # lesson time
    target, _ = path_cents(lesson_path, t - lag)   # the singer follows `lag` seconds late
    c = target + offset
    if note_offsets:
        for step, off in note_offsets.items():
            c = np.where(np.abs(target - step_cents(step)) < 1, c + off, c)
    c = c + vib * np.sin(2 * np.pi * 5.5 * t) + np.cumsum(rng.normal(0, 0.02, n)).clip(-4, 4)
    amp = np.ones(n)
    if loud_top_db:
        lo, hi = np.nanmin(target), np.nanmax(target)
        amp *= 10 ** (loud_top_db * np.nan_to_num((target - lo) / max(1, hi - lo)) / 20)
    if dyn:
        ts, gs = zip(*dyn)
        g = np.interp(t - lag, ts, gs)
        amp *= g
        if drift_with_loud:
            c = c + drift_with_loud * (g - min(gs)) / (max(gs) - min(gs))
    for g0, g1 in gaps:
        c[(t >= g0) & (t < g1)] = np.nan
    return voice(c, amp, sa, vowel, rng, trill)

def hiss(seconds, rng, uneven_db=0.0):
    n = int((LEAD + seconds + 1.5) * SR)
    t = np.arange(n) / SR - LEAD
    on = (t >= 0.3) & (t < 0.3 + seconds)
    env = np.convolve(on.astype(float), np.hanning(int(0.1 * SR)) / (0.05 * SR), mode='same')
    if uneven_db:
        env *= 10 ** (uneven_db * np.sin(2 * np.pi * 0.4 * t) / 20)
    s = sosfilt(butter(4, 3500, 'hp', fs=SR, output='sos'), rng.normal(0, 1, n)) * env
    return s

def write(name, x, lesson, sa, expect, rng, snr=25):
    d = os.path.join(HERE, 'cases_lessons', name); os.makedirs(d, exist_ok=True)
    act = x[int(LEAD * SR):]
    ref = rms(act[np.abs(act) > 0.02 * np.max(np.abs(act))])
    x = phone(x, rng, snr, ref)
    x.astype(np.float32).tofile(os.path.join(d, 'audio.f32'))
    json.dump({'sr': SR, 'sa_hz': sa, 'lesson': lesson, 'start': LEAD, 'expect': expect}, open(os.path.join(d, 'meta.json'), 'w'))
    print('wrote', name)

# lesson paths (copied from the app; evaluate_lessons.py checks they still match)
P = {
    'hum': [[0, 5]],
    'trill': [[0, 1], [7, 1.5, 1], [7, 0.5], [0, 1.5, 1], [0, 0.5]],
    'five': [[0, .8], [2, .8], [4, .8], [5, .8], [7, 1.2], [5, .8], [4, .8], [2, .8], [0, 1.2]],
    'meend': [[0, 1], [4, 1.2, 1], [4, 1], [0, 1.2, 1], [0, 1]],
    'swell': [[0, 6]],
    'staccato': [[0, .35], [None, .35], [4, .35], [None, .35], [7, .35], [None, .35], [4, .35], [None, .35], [0, .5]],
    'low': [[0, 1], [-1, .8], [-3, .8], [-5, 1.5], [-3, .8], [-1, .8], [0, 1.2]],
    'high': [[7, 1], [9, .8], [11, .8], [12, 1.5], [11, .8], [9, .8], [7, 1.2]],
}
SWELL_DYN = [[0, .15], [3, 1], [6, .15]]

def main():
    M, F = note_hz('C', 3), note_hz('A', 3)
    r = lambda s: np.random.default_rng(s)
    write('five_good', sing_lesson(P['five'], M, r(1)), 'five', M, {'score_min': 85, 'no_tip': ['flat', 'sharp', 'louder', 'broke']}, r(1))
    write('five_flat', sing_lesson(P['five'], M, r(2), offset=-60), 'five', M, {'score_max': 35, 'tip': ['flat']}, r(2))
    write('five_ga_flat', sing_lesson(P['five'], M, r(3), note_offsets={4: -28}), 'five', M, {'score_min': 70, 'tip': ['Ga was', 'flat']}, r(3))
    write('high_easy_male', sing_lesson(P['high'], M, r(21), vowel='oo'), 'high', M, {'score_min': 80, 'no_tip': ['louder']}, r(21))
    write('high_push_male', sing_lesson(P['high'], M, r(4), vowel='oo', loud_top_db=10), 'high', M, {'tip': ['louder on the high notes']}, r(4))
    write('high_push_female', sing_lesson(P['high'], F, r(5), vowel='oo', loud_top_db=9), 'high', F, {'known_limit': 'a female voice on "oo" loses level naturally above the first formant, which hides 9 dB of pushing'}, r(5))
    write('high_light', sing_lesson(P['high'], M, r(6), vowel='oo', loud_top_db=-2), 'high', M, {'score_min': 80, 'no_tip': ['louder']}, r(6))
    write('low_good', sing_lesson(P['low'], M, r(7)), 'low', M, {'score_min': 80, 'no_tip': ['flat', 'sharp']}, r(7))
    write('low_good_bass', sing_lesson(P['low'], note_hz('A', 2), r(8)), 'low', note_hz('A', 2), {'score_min': 80}, r(8))
    write('meend_smooth', sing_lesson(P['meend'], M, r(9)), 'meend', M, {'score_min': 80, 'tip': ['no breaks']}, r(9))
    write('meend_breaks', sing_lesson(P['meend'], M, r(10), gaps=[(1.6, 1.8), (4.0, 4.25)]), 'meend', M, {'stat_eq': {'breaks': 2}}, r(10))
    write('trill', sing_lesson(P['trill'], M, r(11), vowel='trill', trill=True), 'trill', M, {'score_min': 70}, r(11))
    write('hum', sing_lesson(P['hum'], M, r(12), vowel='mm', vib=3), 'hum', M, {'score_min': 90, 'tip': ['steady']}, r(12))
    write('hum_wobbly', sing_lesson(P['hum'], M, r(13), vowel='mm', vib=22), 'hum', M, {'tip': ['Wobbly']}, r(13))
    write('swell_good', sing_lesson(P['swell'], M, r(14), dyn=SWELL_DYN, vib=4), 'swell', M, {'tip': ['stayed level', 'Good volume']}, r(14))
    write('swell_sharp', sing_lesson(P['swell'], M, r(15), dyn=SWELL_DYN, drift_with_loud=30, vib=4), 'swell', M, {'tip': ['sharp by about']}, r(15))
    write('swell_flat_dyn', sing_lesson(P['swell'], M, r(16), dyn=[[0, .8], [3, 1], [6, .8]], vib=4), 'swell', M, {'tip': ['start softer']}, r(16))
    write('staccato', sing_lesson(P['staccato'], M, r(17), lag=0.12), 'staccato', M, {'stat_eq': {'hits': 5}, 'tip': ['separated']}, r(17))
    # range: siren from mandra Ma (-7) to taar Ga (16), twice
    siren = [[-7, .4], [16, 3, 1], [16, .3], [-7, 3, 1], [-7, .3], [16, 3, 1], [-7, 1.5, 1]]
    write('range_siren', sing_lesson(siren, M, r(18), vowel='oo', lag=0, vib=0), 'range', M,
          {'stat_near': {'low': [step_cents(-7), 60], 'high': [step_cents(16), 60]}}, r(18))
    write('breath_12s', hiss(12, r(19)), 'breath', M, {'stat_near': {'seconds': [12, 0.6]}, 'tip': ['Very even']}, r(19))
    write('breath_uneven', hiss(9, r(20), uneven_db=6), 'breath', M, {'stat_near': {'seconds': [9, 0.8]}, 'tip': ['Uneven']}, r(20))

if __name__ == '__main__':
    main()
