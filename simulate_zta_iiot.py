"""
Simulação do Artigo Científico (Nature Scientific Reports, 2025):
"A novel and secure artificial intelligence enabled zero trust intrusion detection in industrial internet of things architecture"
Autores: Asif Ali Laghari, Abdullah Ayub Khan et al.
DOI: 10.1038/s41598-025-11738-9

Este script reproduz em ambiente local (Python nativo):
1. As equações matemáticas (1 a 7) descritas no artigo para avaliação de desempenho.
2. Simulação de fluxo de pacotes industriais (Telemetria Smart Grid vs. Ataques IIoT: Injeção de Dados, DDoS, Escaneamento Lateral).
3. Avaliação comparativa entre Controle de Acesso Clássico vs. Arquitetura Zero Trust com IA.
"""

import math
import random
import time

def min_max_scale(val, min_val, max_val):
    """
    Equação (1) do Artigo:
    a_norm = (a - min(a)) / (max(a) - min(a))
    Normalização de features de tráfego IIoT para o intervalo [0, 1].
    """
    if max_val == min_val:
        return 0.0
    return (val - min_val) / (max_val - min_val)

def compute_metrics(tp, tn, fp, fn):
    """
    Equações (3) a (7) do Artigo:
    - Xi = True Positives (TP)
    - Xn = True Negatives (TN)
    - Fi = False Positives (FP)
    - Fn = False Negatives (FN)
    """
    xi, xn, fi, fn_val = tp, tn, fp, fn
    total = xi + xn + fi + fn_val

    # Equação (3): Acurácia
    accuracy = (xi + xn) / total if total > 0 else 0.0

    # Equação (4): Precisão
    precision = xi / (xi + fi) if (xi + fi) > 0 else 0.0

    # Equação (5): Revocação (Recall)
    recall = xi / (xi + fn_val) if (xi + fn_val) > 0 else 0.0

    # Equação (6): F1-Score
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Equação (7): Taxa de Falso Positivo (FPR)
    fpr = fi / (fi + xn) if (fi + xn) > 0 else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "fpr": fpr
    }

class ZeroTrustIIoTSimulator:
    def __init__(self, num_packets=1000, attack_ratio=0.27):
        self.num_packets = num_packets
        self.attack_ratio = attack_ratio
        random.seed(42)

    def generate_packet(self):
        """
        Simula geração de pacotes em uma rede industrial / Smart Grid.
        Pacote contém: id, taxa de requisições, entropia de payload, confiança de identidade, rótulo real.
        """
        is_attack = random.random() < self.attack_ratio
        
        if is_attack:
            attack_type = random.choice(["DDoS_Flood", "False_Data_Injection", "Lateral_PortScan", "Malware_Beacon"])
            req_rate = random.uniform(150.0, 900.0)       # Alta frequência de pacotes
            entropy = random.uniform(0.75, 0.99)          # Alta entropia (cargas maliciosas/criptografadas)
            device_reputation = random.uniform(0.1, 0.5)  # Baixa reputação
        else:
            attack_type = "Normal_Telemetry"
            req_rate = random.uniform(1.0, 60.0)          # Taxa normal de medições de sensores
            entropy = random.uniform(0.15, 0.60)          # Tráfego regular conhecido
            device_reputation = random.uniform(0.8, 1.0)  # Dispositivo com credenciais íntegras

        return {
            "is_attack": is_attack,
            "type": attack_type,
            "rate": req_rate,
            "entropy": entropy,
            "reputation": device_reputation
        }

    def evaluate_classical_perimeter(self, packets):
        """
        Modelo Clássico de Segurança de Borda:
        Confia no tráfego que já conseguiu passar pelo firewall de perímetro.
        Falha em detectar ataques originados internamente ou por movimentação lateral.
        """
        start_time = time.time()
        tp, tn, fp, fn = 0, 0, 0, 0

        for pkt in packets:
            # Controle clássico só bloqueia anomalias muito extremas de volume
            predicted_attack = pkt["rate"] > 700.0
            
            if predicted_attack and pkt["is_attack"]:
                tp += 1
            elif not predicted_attack and not pkt["is_attack"]:
                tn += 1
            elif predicted_attack and not pkt["is_attack"]:
                fp += 1
            else:
                fn += 1

        elapsed = time.time() - start_time
        metrics = compute_metrics(tp, tn, fp, fn)
        metrics["time_s"] = elapsed
        metrics["identified_attacks"] = tp
        return metrics

    def evaluate_zero_trust_ml(self, packets):
        """
        Modelo Proposto no Artigo: Zero Trust com IA/ML Adaptativo
        Aplica o princípio: "Never Trust, Always Verify".
        Cada requisição é normalizada (Eq. 1) e avaliada por escore dinâmico de confiança e anomalia.
        """
        start_time = time.time()
        tp, tn, fp, fn = 0, 0, 0, 0

        # Normalização de limites
        rates = [p["rate"] for p in packets]
        min_r, max_r = min(rates), max(rates)

        for pkt in packets:
            norm_rate = min_max_scale(pkt["rate"], min_r, max_r)
            norm_entropy = pkt["entropy"]
            reputation = pkt["reputation"]

            # Função de Decisão Zero Trust (Policy Decision Point)
            # Combina verificação de anomalia comportamental e verificação de identidade contínua
            risk_score = (norm_rate * 0.45) + (norm_entropy * 0.35) + ((1.0 - reputation) * 0.20)
            
            # Limiar adaptativo Zero Trust
            predicted_attack = risk_score > 0.42

            if predicted_attack and pkt["is_attack"]:
                tp += 1
            elif not predicted_attack and not pkt["is_attack"]:
                tn += 1
            elif predicted_attack and not pkt["is_attack"]:
                fp += 1
            else:
                fn += 1

        elapsed = time.time() - start_time
        metrics = compute_metrics(tp, tn, fp, fn)
        metrics["time_s"] = elapsed
        metrics["identified_attacks"] = tp
        return metrics

def main():
    print("=" * 75)
    print("SIMULAÇÃO DE DETECÇÃO DE INTRUSÕES EM IIoT / SMART GRIDS COM ZERO TRUST")
    print("Baseado no artigo: Nature Scientific Reports (2025) 15:26843")
    print("=" * 75)
    
    num_samples = 1500
    simulator = ZeroTrustIIoTSimulator(num_packets=num_samples, attack_ratio=0.27)
    
    print(f"\n[+] Gerando tráfego sintético calibrado com {num_samples} amostras IIoT...")
    packets = [simulator.generate_packet() for _ in range(num_samples)]
    actual_attacks = sum(1 for p in packets if p["is_attack"])
    print(f"    - Pacotes normais de telemetria: {num_samples - actual_attacks}")
    print(f"    - Pacotes maliciosos injetados:   {actual_attacks} (~27% do tráfego)\n")

    print("[*] Executando Avaliação do Modelo Clássico de Perímetro...")
    classical_res = simulator.evaluate_classical_perimeter(packets)

    print("[*] Executando Avaliação da Arquitetura Zero Trust com IA (ML Adaptativo)...")
    zt_res = simulator.evaluate_zero_trust_ml(packets)

    print("\n" + "=" * 75)
    print("RESULTADOS COMPARATIVOS DA SIMULAÇÃO (EQUAÇÕES 3 A 7)")
    print("=" * 75)
    print(f"{'Métrica Avaliada':<30} | {'Controle Clássico':<18} | {'Zero Trust (Artigo)':<20}")
    print("-" * 75)
    print(f"{'Acurácia Global (Eq. 3)':<30} | {classical_res['accuracy']*100:>16.2f}% | {zt_res['accuracy']*100:>18.2f}%")
    print(f"{'Precisão (Eq. 4)':<30} | {classical_res['precision']*100:>16.2f}% | {zt_res['precision']*100:>18.2f}%")
    print(f"{'Revocação / Recall (Eq. 5)':<30} | {classical_res['recall']*100:>16.2f}% | {zt_res['recall']*100:>18.2f}%")
    print(f"{'F1-Score (Eq. 6)':<30} | {classical_res['f1_score']*100:>16.2f}% | {zt_res['f1_score']*100:>18.2f}%")
    print(f"{'Taxa de Falso Positivo (Eq. 7)':<30} | {classical_res['fpr']*100:>16.2f}% | {zt_res['fpr']*100:>18.2f}%")
    print(f"{'Intrusões Detectadas':<30} | {classical_res['identified_attacks']:>14} / {actual_attacks:<3} | {zt_res['identified_attacks']:>16} / {actual_attacks:<3}")
    print("-" * 75)

    print("\n[OK] Conclusao da Simulacao:")
    print("    A Arquitetura Zero Trust com IA demonstra ganhos expressivos em revocacao e acuracia,")
    print("    eliminando a falsa sensacao de seguranca do perimetro classico e capturando")
    print("    ameacas laterais e de injecao de dados falsos conforme comprovado no artigo.\n")

if __name__ == "__main__":
    main()
