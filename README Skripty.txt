README – Příloha k bakalářské práci
Autor: Kryštof Matuška
Téma: Porovnání metrik pro hodnocení úrovně poškození audio signálů
Akademický rok: 2024/2025

STRUKTURA A ÚČEL SKRIPTŮ:

Scripty\Skripty pro poškození audia\
├── main.py
│   ← hlavní řídicí skript: spouští zpracování dat, výpočet metrik a ukládání výstupů
│
├── dataset.py
│   ← načítání datasetu pomocí třídy GTZANDataset (PyTorch Dataset)
│
├── degrade.py
│   ← implementace degradací: dropout, clipping, phase loss, time dropout, kvantizace
│
├── metrics.py
│   ← výpočet metrik kvality: PESQ, STOI, SNR, SDR, FAD
│
├── utils.py
│   ← pomocné funkce pro ukládání .wav, generování waveformů a spektrogramů (.png)
│
└── user_interface.py
    ← interaktivní konzolové rozhraní pro výběr degradací a výpočetního zařízení (CPU/GPU)


1. main.py
   - Hlavní řídicí skript pro zpracování audio signálů.
   - Zajišťuje:
     - načtení datasetu (.wav),
     - výběr degradací (dropout, clipping, kvantizace, atd.),
     - výpočet objektivních metrik (PESQ, STOI, SNR, SDR, FAD),
     - uložení výsledků (audio, grafy, tabulky).
   - Výstupy: "audio/", "graphs/", "metrics/".

2. dataset.py
   - Definuje třídu "GTZANDataset" pro načítání audio souborů.
   - Používá se v "main.py" ve spojení s PyTorch DataLoaderem.

3. degrade.py
   - Obsahuje implementace všech degradací:
     - "dropout", "clipping", "phase_loss", "time_dropout", "quantization".
   - Používá se ve funkci "degrade_signal(...)" v "main.py".

4. metrics.py
   - Výpočet objektivních metrik:
     - PESQ, STOI, SNR, SDR, FAD.
   - Využívá knihovny "pesq", "pystoi", "torchmetrics", "frechet_audio_distance".

5. utils.py
   - Pomocné funkce:
     - "save_audio" (uložení .wav),
     - "plot_waveform" (časový průběh),
     - "plot_spectrogram" (spektrogram, škála -30 dB až +10 dB).

6. user_interface.py
   - Interaktivní konzolové rozhraní:
     - Výběr typu degradace,
     - Výběr zařízení (CPU/GPU).

NÁVAZNOST NA ANALÝZU:

- Skript "main.py" slouží jako řídicí rozhraní pro aplikaci degradací, výpočet metrik a uložení výstupních souborů.
- Výsledky metrik (PESQ, STOI, SNR, SDR, FAD) jsou ukládány do tabulky "audio_metrics objective.xlsx".
- Subjektivní hodnocení je zpracováno a validováno zvlášť v tabulce "test_filtered_reordered1.xlsx".
- Obě tabulky jsou následně analyzovány pomocí skriptu "comparation.py", který:
  - Provádí Spearmanovu korelaci mezi objektivními a subjektivními daty,
  - Vytváří korelační tabulky a bodové grafy s regresivních křivkou.

VÝSTUPY:
Chcete vytvořit strukturovanou složku pro uložení dat? (ano/ne)
└── ano

ZVOLENA_CESTA\UZIVATELSKY_NAZEV_SLOZKY\
├── audio\
│   ├── original\               ← originální (referenční) zvukové soubory (.wav)
│   └── processed\              ← poškozené (degradované) zvukové soubory (.wav)
│
├── graphs\
│   ├── original\               ← waveformy a spektrogramy originálů (.png)
│   └── processed\              ← waveformy a spektrogramy degradací (.png)
│
└── metrics\
    ├── audio_metrics.xlsx      ← tabulka výsledků metrik (Excel)
    └── audio_metrics.csv       ← tabulka výsledků metrik (CSV)

- .wav soubory s originálními a degradovanými nahrávkami,
- Vizualizace (waveformy, spektrogramy, bodové grafy) ve složce "graphs/",
- Tabulky s metrikami a korelacemi ve formátu ".xlsx" a ".csv":
  - "audio_metrics objective.xlsx", "audio_metrics objective1.xlsx",

Všechny skripty byly testovány a odpovídají popisu v bakalářské práci.