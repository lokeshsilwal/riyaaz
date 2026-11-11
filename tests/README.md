# Riyaaz test bench

These tests check the app's pitch tracking and practice scoring with synthetic singing whose answers are known. Scoring uses mir_eval. The tests load the pitch code directly from `../index.html`, between the `RIYAAZ CORE START/END` markers. That means they always test the file you upload.

## Setup

You need Node 18 or later, Python 3, and these packages:

    pip install numpy scipy mir_eval

## Run

    python3 synth.py      # makes cases/ (about 1.5 minutes, about 170 MB; not needed in the repo)
    python3 evaluate.py   # prints scores and writes results.md

`evaluate.py` compares two versions:

- **baseline:** plain YIN, the first version.
- **app:** the current tracker.

Run it before and after every change to the tracker.

## Test cases

- **Singers:** a male voice with Sa at C3, a female voice with Sa at A3, and a low male voice with Sa at A2. They sing Yaman, Bhopali, Bhimpalasi and Bhairav phrases, with vibrato, meend, sargam consonants and breath noise.
- **Deliberate detuning:** every note is sung off-centre by a known amount, up to ±25¢.
- **Recording conditions:** clean; phone mic (low-cut filter plus room noise); reverb.
- **Tanpura bleed:** the app's own tanpura, played through a simulated phone speaker at −12 dB and −6 dB relative to the voice.
- **Practice runs:** Yaman, Bhopali and Bhairav sung with held notes. These check that the sharp/flat offset the app reports matches the offset that was actually sung.

## Other scripts

- `sweep.py` tries tracker parameters (for example `yinThreshold`, `tanK`) on the tanpura cases.
- `run_tracker.js`, `run_judge.js` and `render_tanpura.js` are small Node runners that `evaluate.py` and `synth.py` call.
