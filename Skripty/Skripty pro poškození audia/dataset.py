import os
from torch.utils.data import Dataset
import torch
import torchaudio
import pandas as pd
from torch.utils.data import Dataset, DataLoader


class GTZANDataset(Dataset):
    def __init__(self, dataset_path, transform=None):
        self.dataset_path = dataset_path
        self.transform = transform
        self.files = []
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                if file.endswith(".wav"):
                    self.files.append(os.path.join(root, file))

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        waveform, sample_rate = torchaudio.load(self.files[idx])
        if self.transform:
            waveform = self.transform(waveform)
        return waveform, sample_rate, os.path.basename(self.files[idx])
