README – Příloha k bakalářské práci
Autor: Kryštof Matuška
Téma: Porovnání metrik pro hodnocení úrovně poškození audio signálů
Akademický rok: 2024/2025

PŘEHLED SKRIPTU:
- comparation.py
  → Hlavní skript pro porovnání objektivních metrik a subjektivního poslechového hodnocení.
  → Zajišťuje:
    - načtení dat ze souborů (objektivní metriky, subjektivní skóre),
    - odstranění hodnotitelů, kteří nepřiřadili skryté referenční nahrávce hodnocení vyšší jak 90,
    - filtrování požadovaných typů degradací (clipping, dropout, quantize),
    - výpočet Spearmanovy korelace pro každou metriku zvlášť i kombinovaně,
    - vygenerování scatterplotů a regresních křivek,
    - export korelačních tabulek pro každý typ degradace.

VSTUPNÍ SOUBORY:
- audio_metrics objective.xlsx
- audio_metrics objective1.xlsx
- test_filtered_reordered1.xlsx

Soubor "audio_metrics objective.xlsx" obsahuje všechny metriky (včetně SNR, SDR, FAD).  
Soubor "audio_metrics objective1.xlsx" obsahuje pouze řečové metriky (PESQ, STOI).  
Soubor "test_filtered_reordered1.xlsx" obsahuje výsledky subjektivního poslechového testu.

VÝSTUPNÍ STRUKTURA:
Výstupy se ukládají do následujících složek:

- comparison_graphs_grouped/
  - Bodové grafy, regresní křivky (.svg, .png)

- comparison_tables_grouped/
  - Tabulky s daty pro každou metriku a degradaci (.xlsx)

- merged_metrics_speech.xlsx
  → Sloučená data řečových metrik + subjektivní skóre

- merged_metrics_all.xlsx
  → Sloučená data všech metrik + subjektivní skóre

ZPŮSOB SPUŠTĚNÍ:
Skript spustíte v prostředí Python 3.12 pomocí příkazu:

python comparation.py

Před spuštěním upravte cesty ke vstupním souborům podle vaší adresářové struktury ("pd.read_excel(...)").

POUŽITÁ METODA KORELACE:
- Spearmanova korelace ("scipy.stats.spearmanr")
  → Použita pro všechny metriky (PESQ, STOI, FAD, SDR, SNR)
  → Výpočet probíhá samostatně pro řeč i celková data

POŽADAVKY:
- Python 3.12+
- Knihovny:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - scipy
  - openpyxl

Doporučeno spouštět v prostředí jako je PyCharm.