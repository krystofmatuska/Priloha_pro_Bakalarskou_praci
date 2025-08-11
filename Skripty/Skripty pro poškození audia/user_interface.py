import os
import torch


def get_degradation_choices():
    degradations = []
    print("Zadejte více typů poškození. Až skončíte, zadejte 'konec'.")

    while True:
        print("\n1. Dropout\n2. Clipping\n3. Phase Loss\n4. Time Dropout\n5. Kvantizace")
        while True:
            user_choice = input("Vyber typ poškození (1–5) nebo 'konec': ").strip()
            if user_choice.lower() == "konec":
                return degradations
            elif user_choice in ["1", "2", "3", "4", "5"]:
                break
            else:
                print("Neplatná volba. Prosím, zadejte číslo mezi 1 a 5, nebo 'konec'.")

        if user_choice == "1":
            while True:
                try:
                    rate = float(input("Míra výpadku (0.00–1.00): "))
                    if 0 <= rate <= 1:
                        break
                    else:
                        print("Míra výpadku musí být mezi 0.00 a 1.00.")
                except ValueError:
                    print("Neplatný vstup. Prosím, zadejte číslo mezi 0.00 a 1.00.")
            degradations.append(("dropout", {"rate": rate}))

        elif user_choice == "2":
            while True:
                try:
                    sdr_target = float(input("SDR target (0–60): "))
                    if 0 <= sdr_target <= 60:
                        break
                    else:
                        print("SDR target musí být mezi 0 a 60.")
                except ValueError:
                    print("Neplatný vstup. Prosím, zadejte číslo mezi 0 a 60.")
            degradations.append(("clipping", {"SDRtarget": sdr_target}))


        elif user_choice == "3":
            while True:
                try:
                    degree = int(input("Ztráta fáze (0 - bez degradace, 1 - ztráta fáze): "))
                    if degree in [0, 1]:

                        break
                    else:
                        print("Neplatná volba. Zadejte 0 nebo 1.")
                except ValueError:
                    print("Neplatný vstup. Prosím, zadejte číslo 0 nebo 1.")
            degradations.append(("phase_loss", {"phase_loss_degree": degree}))


        elif user_choice == "4":
            while True:
                try:
                    ms = float(input("Délka jednoho výpadku v ms: "))
                    if ms > 0:
                        break
                    else:
                        print("Délka musí být kladná.")
                except ValueError:
                    print("Zadejte číslo.")

            while True:
                try:
                    num = int(input("Počet výpadků v rámci nahrávky: "))
                    if num > 0:
                        break
                    else:
                        print("Počet musí být kladný.")
                except ValueError:
                    print("Zadejte celé číslo.")

            while True:
                fill = input("Typ výplně (zero / noise): ").strip().lower()
                if fill in ["zero", "noise"]:
                    break
                else:
                    print("Zadejte 'zero' nebo 'noise'.")

            degradations.append((
                "time_dropout",
                {   "dropout_time_ms": ms,"num_dropouts": num, "fill_mode": fill }
            ))


        elif user_choice == "5":
            while True:
                try:
                    bit_depth = int(input("Bitová hloubka (1–24): "))
                    if 1 <= bit_depth <= 24:
                        break
                    else:
                        print("Bitová hloubka musí být mezi 1 a 24.")
                except ValueError:
                    print("Neplatný vstup. Prosím, zadejte celé číslo mezi 1 a 24.")
            degradations.append(("quantization", {"bit_depth": bit_depth}))

    return degradations


def get_device_choice():
    while True:
        print("Vyberte zařízení:")
        print("1 - CPU")
        print("2 - GPU")
        user_input = input("Zadejte číslo (1 nebo 2): ").strip()

        if user_input == "1":
            device = torch.device("cpu")
            print("Vybráno: CPU")
            return device
        elif user_input == "2":
            if torch.cuda.is_available():
                device = torch.device("cuda")
                print("Vybráno: GPU")
                return device
            else:
                print("GPU není dostupné. Prosím zvolte 1 pro CPU.")
        else:
            print("Neplatná volba. Prosím zadejte 1 pro CPU nebo 2 pro GPU (pokud je k dispozici).")
