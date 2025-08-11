import os
import torch
import torchaudio
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
import pandas as pd
from pesq import pesq
from pystoi import stoi
from torchmetrics.audio import SignalNoiseRatio
from frechet_audio_distance import FrechetAudioDistance
from utils import save_audio, plot_waveform, plot_spectrogram
from degrade import degrade_signal
from metrics import calculate_pesq, calculate_stoi, calculate_snr, calculate_sdr, calculate_fad
from dataset import GTZANDataset
from user_interface import get_degradation_choices, get_device_choice
import torchaudio.transforms as T
import tkinter as tk
from tkinter import filedialog, simpledialog


def get_user_input(prompt):
    while True:
        user_input = input(prompt).strip().lower()
        if user_input == 'ano':
            return True
        elif user_input == 'ne':
            return False
        else:
            print("Neplatná volba. Prosím, zadejte 'ano' nebo 'ne'.")

print("Dobrý den, vítejte na programu pro ověřování objektivních metrik!")
CREATE_STRUCTURE = get_user_input("Chcete vytvořit strukturovanou složku pro uložení dat? (ano/ne): ")
WRITE_METRICS = get_user_input("Chcete zobrazit metriky v konzole? (ano/ne): ")
SAVE_ORIGINAL_AUDIO = get_user_input("Chcete uložit originální audio soubory? (ano/ne): ")
SAVE_GRAPHS = get_user_input("Chcete uložit grafy? (ano/ne): ")
SAVE_METRICS = get_user_input("Chcete uložit metriky? (ano/ne): ")

def select_directory(title="Vyberte složku"):
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title=title) or None

def save_metrics(metrics_df, excel_dir):
    try:
        excel_file = os.path.join(excel_dir, "audio_metrics.xlsx")
        csv_file = os.path.join(excel_dir, "audio_metrics.csv")
        metrics_df.to_excel(excel_file, index=False)
        metrics_df.to_csv(csv_file, index=False)
        if WRITE_METRICS:
            print(f"Výsledky metrik uloženy:\n- {excel_file}\n- {csv_file}")
    except Exception as e:
        print(f"Chyba při ukládání metrik: {e}")

def is_valid_audio_dir(directory):
    return all(f.endswith(".wav") for f in os.listdir(directory))

def get_fad_directories():
    while True:
        print("\nVyberte složky pro výpočet FAD (Frechet Audio Distance):")
        ref_dir = select_directory("Vyberte složku s referenčními audio nahrávkami (složka, ve které se budou ukládat originální audio nahrávkami)")
        eval_dir = select_directory("Vyberte složku s degradovanými audio nahrávkami (složka, ve které se budou ukládat degradované audio nahrávkami)")

        if not ref_dir or not eval_dir:
            print("Nebyla vybrána jedna nebo obě složky pro FAD.")
            retry = input("Chcete zopakovat výběr (1) nebo pokračovat bez FAD (2)? ").strip()
            if retry == "1":
                continue
            elif retry == "2":
                print("FAD metrika bude přeskočena.")
                return None, None
            else:
                print("Neplatná volba. Zadejte 1 nebo 2.")
                continue

        if not is_valid_audio_dir(ref_dir) or not is_valid_audio_dir(eval_dir):
            print("Jedna ze složek neobsahuje pouze .wav soubory. Zkuste to znovu.")
            continue

        print("Složky pro FAD úspěšně vybrány.")
        return ref_dir, eval_dir


if CREATE_STRUCTURE:
    base_dir = select_directory("Vyberte složku, kam se má uložit struktura")
    if base_dir:
        root = tk.Tk()
        root.withdraw()
        structure_name = simpledialog.askstring("Název složky", "Zadejte název pro hlavní složku:")
        if structure_name:
            full_path = os.path.join(base_dir, structure_name)
            graph_dir = os.path.join(full_path, "graphs")
            audio_dir = os.path.join(full_path, "audio")
            excel_dir = os.path.join(full_path, "metrics")
            output_dir = audio_dir

            os.makedirs(os.path.join(graph_dir, "original"), exist_ok=True)
            os.makedirs(os.path.join(graph_dir, "processed"), exist_ok=True)
            os.makedirs(os.path.join(audio_dir, "original"), exist_ok=True)
            os.makedirs(os.path.join(audio_dir, "processed"), exist_ok=True)
            os.makedirs(excel_dir, exist_ok=True)

            print(f"Struktura '{structure_name}' vytvořena v '{base_dir}'.")

            dataset_path = select_directory("Vyberte složku s původními audio nahrávkami")
        else:
            print("Nebyl zadán název složky. Struktura nebude vytvořena.")
    else:
        print("Nebyla vybrána cílová složka. Struktura nebude vytvořena.")
else:
    if SAVE_ORIGINAL_AUDIO or SAVE_GRAPHS or SAVE_METRICS:
        while True:
            dataset_path = select_directory("Vyberte složku s původními audio nahrávkami")
            output_dir = select_directory("Vyberte složku pro výstupní nahrávky (vytvoří se složky original a processed)")

            if SAVE_ORIGINAL_AUDIO:
                audio_dir = select_directory("Vyberte složku s uloženými originálními audio nahrávkami")
            else:
                audio_dir = None

            if SAVE_GRAPHS:
                graph_dir = select_directory("Vyberte složku pro grafy (vytvoří se složky original a processed)")
            else:
                graph_dir = None

            if SAVE_METRICS:
                excel_dir = select_directory("Vyberte složku pro Excel tabulku")
            else:
                excel_dir = None

            if all([dataset_path, output_dir]) and \
               (SAVE_ORIGINAL_AUDIO and audio_dir or not SAVE_ORIGINAL_AUDIO) and \
               (SAVE_GRAPHS and graph_dir or not SAVE_GRAPHS) and \
               (SAVE_METRICS and excel_dir or not SAVE_METRICS):
                break
            else:
                print("Nebyla vybrána některá ze složek.")
                user_input = input("Chcete pokračovat bez nevybrané složky? (1 - pokračovat, 2 - znovu vybrat): ").strip()

                if user_input == "1":
                    print("Pokračuji bez výběru složky.")
                    break
                elif user_input == "2":
                    print("Zopakování výběru složek.")
                    continue
                else:
                    print("Neplatná volba. Zadejte 1 pro pokračování nebo 2 pro zopakování.")
                    continue
    else:
        dataset_path = select_directory("Vyberte složku s původními audio nahrávkami")
        output_dir = None
        audio_dir = None
        graph_dir = None
        excel_dir = None

fad_ref_dir, fad_eval_dir = get_fad_directories()
use_fad = bool(fad_ref_dir and fad_eval_dir)

device = get_device_choice()
degradation_choices = get_degradation_choices()

gtzan_dataset = GTZANDataset(dataset_path, transform=None)
data_loader = DataLoader(gtzan_dataset, batch_size=1, shuffle=False)

metrics_df = pd.DataFrame(columns=["File Name", "Typ", "PESQ", "STOI", "SNR", "FAD", "SDR"])


def normalize_waveform(waveform):
    if waveform.dim() == 2 and waveform.shape[0] == 2:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    elif waveform.dim() == 3 and waveform.shape[1] == 2:
        waveform = torch.mean(waveform, dim=1, keepdim=True)

    if waveform.dim() == 3:
        waveform = waveform.squeeze(0)
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    elif waveform.dim() == 2 and waveform.shape[0] == 1:
        waveform = waveform.squeeze(0).unsqueeze(0)

    return waveform / torch.max(torch.abs(waveform))


for i, (waveform, sample_rate, file_name) in enumerate(data_loader):
    try:
        waveform = normalize_waveform(waveform.to(device))

        if sample_rate != 16000:
            resampler = T.Resample(orig_freq=sample_rate, new_freq=16000).to(device)
            waveform = resampler(waveform)
            sample_rate = 16000

        if SAVE_ORIGINAL_AUDIO:
            filename_clean = os.path.splitext(file_name[0])[0]
            save_audio(waveform.cpu(), sample_rate, f"original_{filename_clean}", output_dir, file_type="original")

            if SAVE_GRAPHS:
                plot_waveform(waveform.cpu(), sample_rate=sample_rate, title=f"Original {filename_clean}", file_name=f"original_{filename_clean}", output_dir=graph_dir, file_type="original")
                plot_spectrogram(waveform.cpu(), sample_rate=sample_rate, title=f"Original {filename_clean} Spectrogram", file_name=f"original_{filename_clean}", output_dir=graph_dir, file_type="original")

        pesq_score = calculate_pesq(waveform.cpu(), waveform.cpu(), sample_rate)
        stoi_score = calculate_stoi(waveform.cpu(), waveform.cpu(), sample_rate)
        snr_score = calculate_snr(waveform.cpu(), waveform.cpu())
        sdr_score = calculate_sdr(waveform.cpu(), waveform.cpu())
        fad_score = 0.00

        if WRITE_METRICS:
            print(f"\n--- Originál: {file_name[0]} ---")
            print(f"PESQ:        {pesq_score:.4f}")
            print(f"STOI:        {stoi_score:.4f}")
            print(f"SNR:         {snr_score:.4f}")
            print(f"FAD:         {fad_score:.4f}")
            print(f"SDR:         {sdr_score:.4f}")
            print("-" * 40)

        metrics_df = pd.concat([metrics_df, pd.DataFrame(
            {"File Name": [f"original_{os.path.splitext(file_name[0])[0]}"], "Typ": ["original"], "PESQ": [pesq_score], "STOI": [stoi_score],
             "SNR": [snr_score], "FAD": [fad_score], "SDR": [sdr_score]})], ignore_index=True)

        for idx, (degradation_type, params) in enumerate(degradation_choices):
            if degradation_type in ["time_dropout", "phase_loss"]:
                params["sample_rate"] = sample_rate
            degraded = degrade_signal(waveform, degradation_type=degradation_type, **params)
            degraded = normalize_waveform(degraded)

            degradation_info = "_".join([f"{key}_{value}" for key, value in params.items()])
            suffix = f"{degradation_type}_{degradation_info}_{os.path.splitext(file_name[0])[0]}"
            save_audio(degraded.cpu(), sample_rate, suffix, output_dir, file_type="processed")

            if SAVE_GRAPHS:
                plot_waveform(degraded.cpu(), sample_rate=sample_rate, title=f"{degradation_type} {file_name[0]}", file_name=suffix, output_dir=graph_dir, file_type="processed")
                plot_spectrogram(degraded.cpu(), sample_rate=sample_rate, title=f"{degradation_type} {file_name[0]} Spectrogram", file_name=suffix, output_dir=graph_dir, file_type="processed")

            pesq_score = calculate_pesq(waveform.cpu(), degraded.cpu(), sample_rate)
            stoi_score = calculate_stoi(waveform.cpu(), degraded.cpu(), sample_rate)
            snr_score = calculate_snr(waveform.cpu(), degraded.cpu())
            sdr_score = calculate_sdr(waveform.cpu(), degraded.cpu())
            fad_score = calculate_fad(fad_ref_dir, fad_eval_dir) if use_fad else 0.0

            if WRITE_METRICS:
                print(f"\n--- Degradace: {degradation_type} ---")
                print(f"Soubor: {file_name[0]}")
                print(f"PESQ:        {pesq_score:.4f}")
                print(f"STOI:        {stoi_score:.4f}")
                print(f"SNR:         {snr_score:.4f}")
                print(f"FAD:         {fad_score:.4f}")
                print(f"SDR:         {sdr_score:.4f}")
                print("-" * 40)

            metrics_df = pd.concat([metrics_df, pd.DataFrame(
                {"File Name": [f"{degradation_type}_{degradation_info}_{os.path.splitext(file_name[0])[0]}"],
                 "Typ": [degradation_type],
                 "PESQ": [pesq_score],
                 "STOI": [stoi_score],
                 "SNR": [snr_score],
                 "FAD": [fad_score],
                 "SDR": [sdr_score]})], ignore_index=True)

    except Exception as e:
        print(f"Chyba při zpracování {file_name[0]}: {e}")
        continue

if SAVE_METRICS:
    save_metrics(metrics_df, excel_dir)
elif WRITE_METRICS:
    print("Metriky se neukládají.")