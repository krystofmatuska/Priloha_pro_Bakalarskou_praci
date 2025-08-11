import os
import numpy as np
import torch
import torchaudio
import matplotlib
matplotlib.use('Agg')
from scipy.io.wavfile import write
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def save_audio(waveform, sample_rate, filename, output_dir, file_type="processed", enable=True, verbose=True):
    if not enable:
        return

    folder_path = os.path.join(output_dir, file_type)
    os.makedirs(folder_path, exist_ok=True)

    output_path = os.path.join(folder_path, f"{filename}.wav")

    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            if verbose:
                print(f"Existující soubor byl odstraněn: {output_path}")
        except Exception as e:
            print(f"Chyba při odstraňování souboru {output_path}: {e}")
            return

    try:
        torchaudio.save(output_path, waveform, sample_rate)
        if verbose:
            print(f"Uložen soubor: {output_path}")
    except Exception as e:
        print(f"Chyba při ukládání souboru {output_path}: {e}")


def plot_waveform(waveform, sample_rate, title, file_name, output_dir, file_type="processed", enable=True, verbose=True):
    if not enable:
        return

    folder_path = os.path.join(output_dir, file_type)
    os.makedirs(folder_path, exist_ok=True)

    waveform = waveform.squeeze()
    time_axis = torch.arange(0, waveform.shape[-1]) / sample_rate

    plt.figure()
    plt.plot(time_axis.numpy(), waveform.numpy())
    plt.title(title)
    plt.xlabel("Čas (s)")
    plt.ylabel("Amplituda")

    plt.grid(True)

    output_path = os.path.join(folder_path, f"{file_name}_waveform.png")
    plt.savefig(output_path)
    plt.close()

    if verbose:
        print(f"Waveform uložen do: {output_path}")


def plot_spectrogram(waveform, sample_rate, title, file_name, output_dir,
                     file_type="processed", enable=True, verbose=True):
    if not enable:
        return

    folder_path = os.path.join(output_dir, file_type)
    os.makedirs(folder_path, exist_ok=True)

    n_fft = 1024
    hop_length = 512
    spectrogram = torch.stft(waveform, n_fft=n_fft, hop_length=hop_length, return_complex=True)
    spectrogram_db = 20 * torch.log10(spectrogram.abs() + 1e-6)

    time_len = spectrogram_db.size(2)
    end_cut = int(time_len * 0.05)
    spectrogram_db = spectrogram_db[:, :, :-end_cut] if end_cut > 0 else spectrogram_db

    time_axis = np.arange(spectrogram_db.size(2)) * hop_length / sample_rate
    freq_axis = np.arange(spectrogram_db.size(1)) * sample_rate / n_fft

    # Nastavení podle připomínky vedoucího – rozsah -30 dB až 0 dB
    vmin = -30
    vmax = 10

    plt.figure(figsize=(12, 5))
    plt.pcolormesh(time_axis, freq_axis, spectrogram_db.squeeze().numpy(),
                   shading='gouraud', vmin=vmin, vmax=vmax, cmap='inferno')
    plt.title(title, fontsize=14)
    plt.xlabel("Čas (s)", fontsize=12)
    plt.ylabel("Frekvence (Hz)", fontsize=12)
    plt.colorbar(format="%+2.0f dB", label="Intenzita (dB)")
    plt.tight_layout()

    output_path = os.path.join(folder_path, f"{file_name}_spectrogram.png")
    plt.savefig(output_path, dpi=200)
    plt.close()

    if verbose:
        print(f"Spektrogram uložen do: {output_path}")
