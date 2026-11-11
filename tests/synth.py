"""Synthetic riyaaz recordings with known answers.

Each case is written to cases/<name>/:
  audio.f32   mono float32 at SR
  ref.csv     time,f0 on a 10 ms grid (f0 = 0 where the voice is silent)
  meta.json   Sa, notes sung (step, intentional detune in cents, times), conditions

The singer: additive glottal-style source shaped by vowel formants, sargam
consonant onsets, breath noise, slow pitch drift, vibrato on some notes,
meend (glides) between notes, phrase pauses. Each note is deliberately sung
off-centre by a known amount so the app's sharp/flat reading can be checked.
Conditions: phone-mic low cut, room noise, reverb, tanpura bleed from the
speaker (rendered with the app's own tanpura code).
"""
import json, os, subprocess, sys
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
JUST = [0, 111.73, 203.91, 315.64, 386.31, 498.04, 590.22, 701.96, 813.69, 884.36, 996.09, 1088.27]
NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}

def note_hz(name, octave):
    midi = (octave + 1) * 12 + NOTE[name]
    return 440 * 2 ** ((midi - 69) / 12)

def step_cents(step):
    o, d = divmod(step, 12)
    return o * 1200 + JUST[d]

# raag sequences (same numbers as the app)
YAMAN_UP, YAMAN_DN = [-1, 2, 4, 6, 9, 11, 12], [12, 11, 9, 7, 6, 4, 2, 0]
YAMAN_PAKAD = [-1, 2, 4, 2, -1, 2, 0, 7, 6, 4, 2, 0]
BHOP_UP, BHOP_DN = [0, 2, 4, 7, 9, 12], [12, 9, 7, 4, 2, 0]
BHOP_PAKAD = [4, 2, 0, -3, 0, 2, 4, 7, 4, 9, 7, 4, 2, 0]
BHIM_UP = [-2, 0, 3, 5, 7, 10, 12]
BHAIRAV = [0, 1, 4, 5, 7, 8, 11, 12, 11, 8, 7, 5, 4, 1, 0]
LOW_PHRASE = [0, -1, -3, -5, -7, -5, -3, -1, 0]       # down to mandra Ma and back
HIGH_PHRASE = [7, 9, 11, 12, 14, 16, 19, 16, 14, 12]  # up to taar Pa

SYL = {0: 's', 1: 'r', 2: 'r', 3: 'g', 4: 'g', 5: 'm', 6: 'm', 7: 'p', 8: 'd', 9: 'd', 10: 'n', 11: 'n'}
VOWEL_OF = {0: 'aa', 1: 'e', 2: 'e', 3: 'aa', 4: 'aa', 5: 'aa', 6: 'aa', 7: 'aa', 8: 'aa', 9: 'aa', 10: 'ee', 11: 'ee'}
VOWELS = {  # formant freqs, bandwidths, gains
    'aa': ([730, 1090, 2440, 3400], [90, 110, 160, 250], [1.0, 0.6, 0.25, 0.1]),
    'e':  ([530, 1840, 2480, 3500], [80, 120, 160, 250], [1.0, 0.45, 0.3, 0.1]),
    'ee': ([270, 2290, 3010, 3700], [60, 120, 170, 250], [1.0, 0.35, 0.3, 0.1]),
    'oo': ([300, 870, 2240, 3300], [60, 90, 160, 250], [1.0, 0.4, 0.08, 0.05]),
}

def formant_gain(f, vowel):
    F, B, A = VOWELS[vowel]
    g = 0.03 + np.zeros_like(f)
    for Fi, Bi, Ai in zip(F, B, A):
        g += Ai / np.sqrt(1 + ((f - Fi) / (Bi / 2)) ** 2)  # 2-pole resonance magnitude
    return g

def sing(phrases, sa_hz, rng, hold=(0.5, 1.4), vib_prob=0.4, vib_depth=(15, 35), detune_sd=12,
         detune_max=25, legato=0.6, vowel_override=None):
    """phrases: list of lists of steps. Returns (signal, f0_samples, voiced_mask, notes)."""
    segs_f0, segs_amp, segs_vow, segs_cons, notes = [], [], [], [], []
    t = 0.4
    lead = np.zeros(int(t * SR))
    segs_f0.append(lead); segs_amp.append(lead.copy()); segs_vow.append(np.zeros(len(lead), int)); segs_cons.append(np.zeros(len(lead)))
    vlist = list(VOWELS)
    for phrase in phrases:
        prev_c = None
        for i, step in enumerate(phrase):
            dur = rng.uniform(*hold)
            n = int(dur * SR)
            det = float(np.clip(rng.normal(0, detune_sd), -detune_max, detune_max))
            c = step_cents(step) + det
            tt = np.arange(n) / SR
            cents = np.full(n, c)
            reart = prev_c is None or rng.random() > legato
            # meend from previous note
            if prev_c is not None:
                g = int(rng.uniform(0.07, 0.15) * SR)
                s = np.linspace(0, 1, g); s = s * s * (3 - 2 * s)
                cents[:g] = prev_c + (c - prev_c) * s
            # vibrato
            if rng.random() < vib_prob and dur > 0.6:
                depth = rng.uniform(*vib_depth); rate = rng.uniform(5, 6.5)
                ramp = np.clip((tt - 0.3) / 0.2, 0, 1)
                cents += depth * ramp * np.sin(2 * np.pi * rate * tt)
            # slow drift / jitter (part of the truth)
            drift = np.cumsum(rng.normal(0, 1, n // 480 + 2))[: n // 480 + 2]
            drift = np.interp(np.arange(n), np.arange(len(drift)) * 480, drift - drift.mean()) * 0.8
            cents += np.clip(drift, -6, 6)
            amp = np.ones(n) * rng.uniform(0.7, 1.0)
            cons = np.zeros(n)
            if reart:
                a = int(0.04 * SR); amp[:a] *= np.linspace(0, 1, a)
                cl = int((0.07 if SYL[step % 12] == 's' else 0.025) * SR)
                cons[:cl] = 1
                amp[:cl] = 0  # consonant before the vowel: unvoiced
            if i == len(phrase) - 1:
                r = int(0.08 * SR); amp[-r:] *= np.linspace(1, 0, r)
            elif rng.random() > legato:
                r = int(0.03 * SR); amp[-r:] *= np.linspace(1, 0.3, r)
            vow = vowel_override or (VOWEL_OF[step % 12] if rng.random() < 0.7 else rng.choice(vlist))
            notes.append({'step': step, 'detune': det, 'target': step_cents(step), 'start': t, 'end': t + dur, 'vowel': vow})
            segs_f0.append(sa_hz * 2 ** (cents / 1200)); segs_amp.append(amp)
            segs_vow.append(np.full(n, vlist.index(vow))); segs_cons.append(cons)
            prev_c = c; t += dur
        gap = rng.uniform(0.4, 1.0); g = int(gap * SR)
        segs_f0.append(np.zeros(g)); segs_amp.append(np.zeros(g)); segs_vow.append(np.zeros(g, int)); segs_cons.append(np.zeros(g))
        t += gap
    f0 = np.concatenate(segs_f0); amp = np.concatenate(segs_amp)
    vow = np.concatenate(segs_vow); cons = np.concatenate(segs_cons)
    # carry f0 through silent samples so phase is continuous (amp is 0 there)
    f0_fill = f0.copy(); last = sa_hz
    nz = f0_fill > 0
    idx = np.where(nz, np.arange(len(f0)), 0); np.maximum.accumulate(idx, out=idx)
    f0_fill = np.where(nz, f0_fill, f0_fill[idx]); f0_fill[f0_fill == 0] = sa_hz
    # smooth amplitude a little (avoid clicks)
    k = np.hanning(int(0.01 * SR)); k /= k.sum()
    amp = np.convolve(amp, k, mode='same')
    phase = 2 * np.pi * np.cumsum(f0_fill) / SR
    sig = np.zeros(len(f0))
    K = int(5000 / f0_fill.min())
    for kk in range(1, K + 1):
        fk = kk * f0_fill
        ok = fk < 6000
        if not ok.any(): break
        gain = np.zeros(len(f0))
        for vi, vname in enumerate(vlist):
            m = vow == vi
            if m.any(): gain[m] = formant_gain(fk[m], vname)
        sig += ok * gain * kk ** -1.2 * np.sin(kk * phase)
    sig *= amp
    # breath + consonant noise
    noise = rng.normal(0, 1, len(sig))
    hp = butter(2, 2500, 'hp', fs=SR, output='sos')
    sig += sosfilt(hp, noise) * (cons * 0.25 + amp * 0.012)
    sig = sig / np.max(np.abs(sig)) * 0.5
    voiced = (amp > 0.15) & (f0 > 0)
    return sig, f0, voiced, notes

def pink(n, rng):
    w = rng.normal(0, 1, n)
    X = np.fft.rfft(w); f = np.arange(len(X)); f[0] = 1
    return np.fft.irfft(X / np.sqrt(f), n)

def rms(x): return np.sqrt(np.mean(x ** 2))

def tanpura(sa_hz, first, dur):
    out = f'/tmp/tan_{sa_hz:.2f}_{first}.f32'
    subprocess.run(['node', os.path.join(HERE, 'render_tanpura.js'), str(sa_hz), first, str(SR), str(dur), '4.4', out], check=True)
    return np.fromfile(out, np.float32).astype(np.float64)

def write_case(name, sig, f0, voiced, notes, sa_hz, cond, tan_only=None, extra=None):
    d = os.path.join(HERE, 'cases', name); os.makedirs(d, exist_ok=True)
    sig.astype(np.float32).tofile(os.path.join(d, 'audio.f32'))
    tgrid = np.arange(0, len(sig) / SR, 0.01)
    idx = np.minimum((tgrid * SR).astype(int), len(sig) - 1)
    ref = np.where(voiced[idx], f0[idx], 0)
    np.savetxt(os.path.join(d, 'ref.csv'), np.c_[tgrid, ref], delimiter=',', fmt='%.5f')
    meta = {'sr': SR, 'sa_hz': sa_hz, 'conditions': cond, 'notes': notes}
    if tan_only is not None:
        meta['tanpura_only_frames'] = tan_only[idx].astype(int).tolist()
        apply.tanpura_ref.tofile(os.path.join(d, 'tanpura_ref.f32'))  # the app knows what it is playing
    else:
        p = os.path.join(d, 'tanpura_ref.f32')
        if os.path.exists(p): os.remove(p)
    if extra: meta.update(extra)
    json.dump(meta, open(os.path.join(d, 'meta.json'), 'w'))

def apply(sig, voiced, sa_hz, rng, phone=False, snr=None, reverb=False, tan_db=None, first='P'):
    x = sig.copy(); vr = rms(sig[voiced]) if voiced.any() else rms(sig)
    if reverb:
        n = int(0.6 * SR); ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 6.9 / 0.5)
        ir[0] = 0; ir = ir / np.sqrt(np.sum(ir ** 2)) * 0.5; ir[0] = 1
        x = fftconvolve(x, ir)[: len(x)]
    tan_only = None
    if tan_db is not None:
        tp = tanpura(sa_hz, first, len(x) / SR + 0.1)[: len(x)]
        # what reaches the mic from a phone speaker: no deep bass, ~25 ms later
        spk = sosfilt(butter(2, 350, 'hp', fs=SR, output='sos'), tp)
        spk = np.concatenate([np.zeros(int(0.025 * SR)), spk])[: len(x)]
        x += spk / rms(spk) * vr * 10 ** (tan_db / 20)
        tan_only = ~voiced
        apply.tanpura_ref = (tp / np.max(np.abs(tp)) * 0.5).astype(np.float32)
    if snr is not None:
        p = pink(len(x), rng); x += p / rms(p) * vr * 10 ** (-snr / 20)
    if phone:
        x = sosfilt(butter(2, 200, 'hp', fs=SR, output='sos'), x)
        x = sosfilt(butter(2, 7000, 'lp', fs=SR, output='sos'), x)
    x = x / np.max(np.abs(x)) * 0.7
    return x, tan_only

def main():
    MALE, FEMALE, LOW = note_hz('C', 3), note_hz('A', 3), note_hz('A', 2)
    male_phr = [YAMAN_UP + YAMAN_DN[1:], YAMAN_PAKAD, BHOP_UP + BHOP_DN[1:], BHOP_PAKAD, BHIM_UP, BHAIRAV]
    fem_phr = [BHOP_UP + BHOP_DN[1:], YAMAN_UP + YAMAN_DN[1:], HIGH_PHRASE, YAMAN_PAKAD, BHAIRAV]
    low_phr = [LOW_PHRASE, YAMAN_UP + YAMAN_DN[1:], BHOP_PAKAD, LOW_PHRASE]
    specs = [
        ('male_clean', MALE, male_phr, {}),
        ('female_clean', FEMALE, fem_phr, {}),
        ('low_male_clean', LOW, low_phr, {}),
        ('male_phone_noise', MALE, male_phr, dict(phone=True, snr=20)),
        ('female_phone_noise', FEMALE, fem_phr, dict(phone=True, snr=20)),
        ('low_male_phone', LOW, low_phr, dict(phone=True, snr=25)),
        ('male_reverb', MALE, male_phr, dict(reverb=True, phone=True, snr=30)),
        ('male_tanpura', MALE, male_phr, dict(phone=True, snr=30, tan_db=-12)),
        ('female_tanpura', FEMALE, fem_phr, dict(phone=True, snr=30, tan_db=-12)),
        ('male_tanpura_loud', MALE, male_phr, dict(phone=True, snr=30, tan_db=-6)),
    ]
    for i, (name, sa, phr, cond) in enumerate(specs):
        rng = np.random.default_rng(100 + i)
        sig, f0, voiced, notes = sing(phr, sa, rng)
        x, tan_only = apply(sig, voiced, sa, rng, **cond)
        write_case(name, x, f0, voiced, notes, sa, cond, tan_only)
        print('wrote', name, f'{len(x)/SR:.1f}s')
    # practice runs: long held notes, known detune, for checking the practice-mode scorer
    prac = [
        ('practice_male_yaman', MALE, [YAMAN_UP + YAMAN_DN[1:]], dict(phone=True, snr=30, tan_db=-12)),
        ('practice_female_bhopali', FEMALE, [BHOP_UP + BHOP_DN[1:]], dict(phone=True, snr=25, tan_db=-12)),
        ('practice_low_bhairav', LOW, [BHAIRAV], dict(phone=True, snr=25)),
    ]
    for i, (name, sa, phr, cond) in enumerate(prac):
        rng = np.random.default_rng(500 + i)
        sig, f0, voiced, notes = sing(phr, sa, rng, hold=(1.8, 2.4), vib_prob=0.35, vib_depth=(8, 14),
                                      detune_sd=10, detune_max=18, legato=0.0)
        x, tan_only = apply(sig, voiced, sa, rng, **cond)
        write_case(name, x, f0, voiced, notes, sa, cond, tan_only, extra={'sequence': phr[0]})
        print('wrote', name, f'{len(x)/SR:.1f}s')

if __name__ == '__main__':
    main()
