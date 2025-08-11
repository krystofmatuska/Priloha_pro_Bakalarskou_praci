import librosa
import torchaudio.transforms as T
import torch.nn.functional as F
from scipy.io.wavfile import write
import torch
import torchaudio
import numpy as np
from scipy.optimize import fsolve

def apply_dropout(waveform, rate):
    mask = torch.rand(waveform.shape) > rate
    return waveform * mask

def apply_clipping(waveform, SDRtarget):
    def find_clip_value(thresh):
        xclipped = torch.clamp(waveform, -thresh[0], thresh[0])
        sdr = 20 * np.log10(np.linalg.norm(waveform.numpy()) /
                            (np.linalg.norm(waveform.numpy() - xclipped.numpy()) + 1e-7))
        return np.abs(sdr - SDRtarget)

    init_value = np.array([1.0])
    clip_value = fsolve(find_clip_value, init_value)[0]
    print("Adaptovaný limit pro SDR", clip_value)
    return torch.clamp(waveform, -clip_value, clip_value)

def apply_phase_loss(waveform, sample_rate, phase_loss_degree):
    if phase_loss_degree == 0:
        return waveform

    waveform = waveform.squeeze()

    if waveform.size(0) < 1024:
        padding_size = 1024 - waveform.size(0)
        waveform = torch.nn.functional.pad(waveform, (0, padding_size))

    n_fft = 1024
    hop_length = n_fft // 4
    win_length = n_fft
    window = torch.hann_window(win_length, device=waveform.device)

    D = torch.stft(
        waveform,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        window=window,
        return_complex=True
    )

    if phase_loss_degree == 1:
        D_no_phase = torch.abs(D) * torch.exp(1j * torch.zeros_like(D))
    else:
        print("Neplatný parametr ztráty fáze. Povolené hodnoty: 0 nebo 1.")
        return waveform

    waveform_reconstructed = torch.istft(
        D_no_phase,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        window=window,
        length=waveform.size(0)
    )

    waveform_reconstructed = waveform_reconstructed.unsqueeze(0).unsqueeze(0)
    return waveform_reconstructed

def apply_time_dropout(waveform, dropout_time_ms, sample_rate, num_dropouts=1, fill_mode="zero", silence_threshold=1e-6):

    waveform = waveform.clone()
    num_samples_to_drop = int((dropout_time_ms / 1000) * sample_rate)
    total_samples = waveform.shape[-1]

    if num_samples_to_drop >= total_samples:
        return torch.zeros_like(waveform)

    applied = 0
    max_attempts = num_dropouts * 20
    used_ranges = []
    attempts = 0

    while applied < num_dropouts and attempts < max_attempts:
        max_start = total_samples - num_samples_to_drop
        start_idx = torch.randint(0, max_start, (1,)).item()
        end_idx = start_idx + num_samples_to_drop

        if any(s < end_idx and e > start_idx for s, e in used_ranges):
            attempts += 1
            continue

        segment = waveform[..., start_idx:end_idx]
        energy = torch.sum(segment ** 2).item()

        if energy < silence_threshold:
            attempts += 1
            continue

        if fill_mode == "zero":
            segment.zero_()
        elif fill_mode == "noise":
            noise = torch.randn_like(segment) * 0.01
            segment.copy_(noise)
        else:
            raise ValueError("Neplatný fill_mode. Použij 'zero' nebo 'noise'.")

        used_ranges.append((start_idx, end_idx))
        applied += 1
        attempts += 1

    return waveform

def apply_quantize_signal(waveform, bit_depth):
    num_levels = 2 ** bit_depth

    waveform_norm = (waveform + 1) / 2
    waveform_quantized = torch.round(waveform_norm * (num_levels - 1)) / (num_levels - 1)
    waveform_quantized = waveform_quantized * 2 - 1

    return waveform_quantized

def degrade_signal(waveform, degradation_type, **kwargs):
    if degradation_type == "dropout":
        return apply_dropout(waveform, kwargs.get("rate", 0.2))
    elif degradation_type == "clipping":
        return apply_clipping(waveform, kwargs.get("threshold", 0.2))
    elif degradation_type == "phase_loss":
        return apply_phase_loss(waveform, kwargs.get("sample_rate"), kwargs.get("phase_loss_degree", 45))
    elif degradation_type == "time_dropout":
        return apply_time_dropout(waveform, kwargs.get("dropout_time_ms", 50), kwargs.get("sample_rate"), kwargs.get("num_dropouts", 1), kwargs.get("fill_mode", "zero"), kwargs.get("silence_threshold", 1e-6))
    elif degradation_type == "quantization":
        return apply_quantize_signal(waveform, kwargs.get("bit_depth", 8))
    else:
        raise ValueError(f"Neplatný typ poškození: {degradation_type}")

