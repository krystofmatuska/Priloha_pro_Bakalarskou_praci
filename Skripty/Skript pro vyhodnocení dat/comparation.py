import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import os

obj_speech_df = pd.read_excel(r"C:\Users\Kryštof\Desktop\audio_metrics objective1.xlsx")
obj_all_df = pd.read_excel(r"C:\Users\Kryštof\Desktop\audio_metrics objective.xlsx")
subj_df = pd.read_excel(r"C:\Users\Kryštof\Desktop\test_filtered_reordered1.xlsx")

listener_means = subj_df.groupby("name")["rating_score"].mean()
global_mean = listener_means.mean()
std_dev = listener_means.std()
outliers = listener_means[(listener_means < global_mean - 2 * std_dev) | (listener_means > global_mean + 2 * std_dev)].index.tolist()
print("Vyřazení posluchači:", outliers)

subj_df = subj_df[~subj_df["name"].isin(outliers)]

obj_speech_df = obj_speech_df.rename(columns={"degradation": "stimulus"})
obj_all_df = obj_all_df.rename(columns={"degradation": "stimulus"})
subj_df = subj_df.rename(columns={"rating_stimulus": "stimulus", "rating_score": "MUSHRA"})

subj_df = subj_df[subj_df["stimulus"] != "reference"]

valid_order = [
    "clipping 1", "clipping 3", "clipping 7",
    "dropout 0,1", "dropout 0,05", "dropout 0,01",
    "quantize 3", "quantize 6", "quantize 8"
]

subj_df = subj_df[subj_df["stimulus"].isin(valid_order)]
obj_speech_df = obj_speech_df[obj_speech_df["stimulus"].isin(valid_order)]
obj_all_df = obj_all_df[obj_all_df["stimulus"].isin(valid_order)]

subj_df["stimulus"] = pd.Categorical(subj_df["stimulus"], categories=valid_order, ordered=True)
obj_speech_df["stimulus"] = pd.Categorical(obj_speech_df["stimulus"], categories=valid_order, ordered=True)
obj_all_df["stimulus"] = pd.Categorical(obj_all_df["stimulus"], categories=valid_order, ordered=True)

merged_speech = pd.merge(obj_speech_df, subj_df, on=["trial_id", "stimulus"])
merged_all = pd.merge(obj_all_df, subj_df, on=["trial_id", "stimulus"])

output_dir = "comparison_graphs_grouped"
tables_dir = "comparison_tables_grouped"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(tables_dir, exist_ok=True)

degradation_types = {
    "clipping": ["clipping 1", "clipping 3", "clipping 7"],
    "dropout": ["dropout 0,1", "dropout 0,05", "dropout 0,01"],
    "quantize": ["quantize 3", "quantize 6", "quantize 8"]
}

speech_metrics = ["PESQ", "STOI"]
all_metrics = ["SNR", "FAD", "SDR"]

def get_legend_labels(degradation_key):
    if degradation_key == "clipping":
        return {
            "clipping 1": "Clipping 1 dB",
            "clipping 3": "Clipping 3 dB",
            "clipping 7": "Clipping 7 dB"
        }
    elif degradation_key == "dropout":
        return {
            "dropout 0,1": "Dropout 10 %",
            "dropout 0,05": "Dropout 5 %",
            "dropout 0,01": "Dropout 1 %"
        }
    elif degradation_key == "quantize":
        return {
            "quantize 3": "3 bity",
            "quantize 6": "6 bitů",
            "quantize 8": "8 bitů"
        }
    else:
        return {}

# Vykreslení grafu
def plot_degradation_comparison(df, degradation_key, metric, target):
    subset = df[df["stimulus"].isin(degradation_types[degradation_key])].copy()
    if subset.empty or metric not in subset.columns:
        return

    correlation, pvalue = spearmanr(subset[metric], subset["MUSHRA"])

    mean_df = subset.groupby(["name", "stimulus"])[[metric, "MUSHRA"]].mean().reset_index()

    mean_df["stimulus"] = pd.Categorical(mean_df["stimulus"], categories=degradation_types[degradation_key], ordered=True)

    plt.figure(figsize=(8, 4.5))
    sns.scatterplot(data=mean_df, x=metric, y="MUSHRA", hue="stimulus", palette="Set2", edgecolor="black", s=60)
    sns.regplot(data=mean_df, x=metric, y="MUSHRA", scatter=False, lowess=True, color="blue", line_kws={'linewidth': 2})

    plt.title(f"{degradation_key.capitalize()} – {metric} vs Poslechový test\nSpearman ρ = {correlation:.3f}, p-hodnota = {pvalue:.3f}")
    plt.xlabel(metric)
    plt.ylabel("MUSHRA skóre")
    plt.grid(True)

    handles, labels = plt.gca().get_legend_handles_labels()
    label_map = get_legend_labels(degradation_key)
    relevant_stimuli = degradation_types[degradation_key]
    filtered = [(h, label_map.get(l, l)) for h, l in zip(handles, labels) if l in relevant_stimuli]

    if filtered:
        filtered_handles, filtered_labels = zip(*filtered)
        plt.legend(handles=filtered_handles, labels=filtered_labels, title="Úroveň degradace", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.subplots_adjust(right=0.75)
    plt.tight_layout()

    fname = f"{degradation_key}_{metric}_{target}"
    plt.savefig(os.path.join(output_dir, f"{fname}.png"))
    plt.savefig(os.path.join(output_dir, f"{fname}.svg"))
    plt.close()

    print(f"{fname}: Spearman ρ={correlation:.5f}, p-hodnota={pvalue:.3f}")

for degradation in degradation_types:
    for metric in speech_metrics:
        plot_degradation_comparison(merged_speech, degradation, metric, target="speech")

    for metric in all_metrics:
        plot_degradation_comparison(merged_all, degradation, metric, target="all")

def export_metric_table(df, metric, degradation_key, target):
    subset = df[df["stimulus"].isin(degradation_types[degradation_key])]
    if metric not in subset.columns:
        return
    export_df = subset[["stimulus", "trial_id", metric, "MUSHRA"]].dropna().sort_values(by="stimulus")
    fname = f"{degradation_key}_{metric}_{target}.xlsx"
    export_path = os.path.join(tables_dir, fname)
    export_df.to_excel(export_path, index=False)
    print(f"Soubor {fname} byl uložen.")

for degradation in degradation_types:
    for metric in speech_metrics:
        export_metric_table(merged_speech, metric, degradation, target="speech")

    for metric in all_metrics:
        export_metric_table(merged_all, metric, degradation, target="all")

merged_speech.to_excel("merged_metrics_speech.xlsx", index=False)
merged_all.to_excel("merged_metrics_all.xlsx", index=False)
print("Všechny grafy a spojené soubory byly uloženy.")
