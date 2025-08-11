import os
import shutil
from pesq import pesq
from pystoi import stoi
from torchmetrics.audio import SignalNoiseRatio
import numpy as np
import torch
from frechet_audio_distance import FrechetAudioDistance
import tempfile
import uuid

def calculate_fad(reference_dir, evaluation_dir):
    try:
        fad_calculator = FrechetAudioDistance(model_name="vggish", sample_rate=16000, use_pca=False, verbose=False)
        fad_score = fad_calculator.score(reference_dir, evaluation_dir)
        return fad_score
    except Exception as e:
        print(f"Chyba při výpočtu FAD skóre: {e}")
        return None

def calculate_pesq(waveform1, waveform2, sample_rate):
    reference = waveform1[0, 0].numpy() if waveform1.ndimension() == 3 else waveform1.squeeze().numpy()
    degraded = waveform2[0, 0].numpy() if waveform2.ndimension() == 3 else waveform2.squeeze().numpy()
    if reference.ndim != 1 or degraded.ndim != 1:
        print(f"Error: Both signals must be 1D. Reference shape: {reference.shape}, Degraded shape: {degraded.shape}")
        return None

    if sample_rate not in [8000, 16000]:
        print(f"Varování: PESQ vyžaduje vzorkovací kmitočet 8000 nebo 16000 Hz. "
              f"Váš vzorkovací kmitočet je: {sample_rate}. Převádím na 16000 Hz.")
        sample_rate = 16000

    try:
        pesq_score = pesq(sample_rate, reference, degraded, 'wb')
        return pesq_score
    except Exception as e:
        print(f"Chyba vyjadřování PESQ: {e}")
        return None

def calculate_stoi(reference_waveform, degraded_waveform, sample_rate):
    reference = reference_waveform.squeeze().numpy()
    degraded = degraded_waveform.squeeze().numpy()
    return stoi(reference, degraded, sample_rate, extended=False)

def calculate_snr(reference_waveform, degraded_waveform):
    snr_metric = SignalNoiseRatio()
    return snr_metric(reference_waveform, degraded_waveform).item()

def calculate_sdr(original_waveform: torch.Tensor, degraded_waveform: torch.Tensor, mode="truncate") -> float:
    if original_waveform.ndim == 2:
        original_waveform = original_waveform.squeeze(0)
    if degraded_waveform.ndim == 2:
        degraded_waveform = degraded_waveform.squeeze(0)

    len_orig = original_waveform.shape[-1]
    len_deg = degraded_waveform.shape[-1]

    if mode == "truncate":
        min_len = min(len_orig, len_deg)
        s = original_waveform[:min_len]
        s_hat = degraded_waveform[:min_len]
    elif mode == "pad":
        max_len = max(len_orig, len_deg)
        pad_orig = max_len - len_orig
        pad_deg = max_len - len_deg
        s = F.pad(original_waveform, (0, pad_orig))
        s_hat = F.pad(degraded_waveform, (0, pad_deg))
    else:
        raise ValueError("Mode musí být 'truncate' nebo 'pad'.")

    alpha = torch.dot(s, s_hat) / torch.dot(s, s)
    s_target = alpha * s
    e_res = s_hat - s_target

    signal_energy = torch.sum(s_target ** 2)
    error_energy = torch.sum(e_res ** 2)

    if error_energy < 1e-8:
        return float("inf")

    sdr = 10 * torch.log10(signal_energy / (error_energy + 1e-8))
    return sdr.item()

