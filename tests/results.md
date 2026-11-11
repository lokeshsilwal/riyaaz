# Riyaaz pitch-tracking accuracy (synthetic, known answers)

mir_eval.melody metrics in %, RPA/RCA at the standard 50-cent tolerance. 
`≤10¢` / `≤25¢` = share of voiced frames within 10 / 25 cents (what matters for sur). 
`Tan FA` = frames with only the tanpura sounding that were wrongly shown as singing.


## baseline (plain YIN, first version)

| case | RPA | RCA | VR | VFA | OA | median err ¢ | ≤10¢ | ≤25¢ | octave err | Tan FA |
|---|---|---|---|---|---|---|---|---|---|---|
| female_clean | 98.9 | 98.9 | 99.1 | 3.7 | 98.7 | 0.5 | 94.6 | 99.2 | 0.0 | – |
| female_phone_noise | 99.2 | 99.2 | 99.4 | 4.9 | 98.9 | 0.6 | 94.4 | 98.9 | 0.0 | – |
| female_tanpura | 84.6 | 89.9 | 99.1 | 26.1 | 83.9 | 3.0 | 76.8 | 84.4 | 4.5 | 26.1 |
| low_male_clean | 98.7 | 98.7 | 98.7 | 1.6 | 98.7 | 0.4 | 97.3 | 99.9 | 0.0 | – |
| low_male_phone | 99.1 | 99.1 | 99.1 | 1.4 | 99.1 | 0.4 | 96.5 | 99.8 | 0.0 | – |
| male_clean | 99.1 | 99.1 | 99.2 | 2.3 | 99.0 | 0.5 | 95.8 | 99.5 | 0.0 | – |
| male_phone_noise | 99.2 | 99.2 | 99.2 | 1.4 | 99.2 | 0.5 | 95.3 | 99.6 | 0.0 | – |
| male_reverb | 98.6 | 98.6 | 99.2 | 8.4 | 98.0 | 0.7 | 93.0 | 98.0 | 0.0 | – |
| male_tanpura | 83.0 | 91.6 | 97.9 | 31.7 | 82.0 | 2.6 | 78.3 | 83.5 | 9.1 | 31.7 |
| male_tanpura_loud | 36.2 | 58.5 | 74.7 | 60.8 | 36.5 | 78.3 | 39.5 | 46.4 | 28.4 | 60.8 |
| **mean** | **89.7** | 93.3 | 96.6 | 14.2 | **89.4** | 8.8 | 86.1 | 90.9 | 4.2 | 39.5 |

## app

| case | RPA | RCA | VR | VFA | OA | median err ¢ | ≤10¢ | ≤25¢ | octave err | Tan FA |
|---|---|---|---|---|---|---|---|---|---|---|
| female_clean | 98.9 | 98.9 | 99.0 | 3.5 | 98.7 | 0.5 | 94.6 | 99.2 | 0.0 | – |
| female_phone_noise | 99.3 | 99.3 | 99.4 | 4.9 | 98.9 | 0.6 | 94.4 | 99.0 | 0.0 | – |
| female_tanpura | 91.0 | 94.7 | 98.8 | 3.9 | 91.3 | 2.7 | 82.6 | 91.1 | 3.4 | 3.9 |
| low_male_clean | 98.7 | 98.7 | 98.7 | 1.4 | 98.7 | 0.4 | 97.3 | 99.9 | 0.0 | – |
| low_male_phone | 99.1 | 99.1 | 99.1 | 1.1 | 99.1 | 0.4 | 96.4 | 99.7 | 0.0 | – |
| male_clean | 99.1 | 99.1 | 99.1 | 2.0 | 99.0 | 0.5 | 95.8 | 99.5 | 0.0 | – |
| male_phone_noise | 99.2 | 99.2 | 99.2 | 1.4 | 99.1 | 0.5 | 95.3 | 99.6 | 0.0 | – |
| male_reverb | 99.0 | 99.0 | 99.2 | 8.4 | 98.5 | 0.7 | 93.3 | 98.4 | 0.0 | – |
| male_tanpura | 93.2 | 95.6 | 97.0 | 1.5 | 93.6 | 2.2 | 89.1 | 94.8 | 2.5 | 1.5 |
| male_tanpura_loud | 42.7 | 48.5 | 51.6 | 0.6 | 47.6 | 5.7 | 66.1 | 79.5 | 11.4 | 0.6 |
| **mean** | **92.0** | 93.2 | 94.1 | 2.9 | **92.5** | 1.4 | 90.5 | 96.1 | 1.7 | 2.0 |

App tracker: 2048-sample window, 10 ms hop, pitch shown ≈41 ms after it is sung.


## Practice-mode scorer

Each note is scored on its own, as in the app. Singer holds each note ~2 s with a known deliberate offset (±18¢ max) plus vibrato and drift; tolerance 25¢, hold 1 s. 
`offset error` = |offset the app reports − offset actually sung|.

| case | notes completed | mean offset error ¢ | max offset error ¢ |
|---|---|---|---|
| practice_female_bhopali | 10/11 | 2.1 | 3.7 |
| practice_low_bhairav | 15/15 | 1.9 | 3.8 |
| practice_male_yaman | 13/14 | 2.7 | 6.1 |
