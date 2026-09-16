"""
Controlador de API para LM Studio (Llama 1B) com DeepSeek Reasoning Harness
Autor: Benjamin Silva Sergio (UFES / Smart Grids)

Este script:
1. Atua como servidor API local (porta 8000) com suporte completo a CORS para o navegador.
2. Faz a ponte com o servidor local do LM Studio (padrão: http://127.0.0.1:1234/v1).
3. Aplica o DeepSeek Harness no modelo de 1B parâmetros para induzir raciocínio passo a passo (<think>...</think>).
4. Fornece modo de contingência quando o LM Studio estiver temporariamente offline.
"""

import http.server
import json
import socketserver
import urllib.request
import urllib.error
import sys
import os

PORT = 8000
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"

CONTEXT_FACTS = """
FATOS E CONTEXTO DO PROJETO:
- Pesquisador: Benjamin Silva Sergio (Cientista da Computação pela UFES-CEUNES, Mestrando em Engenharia Elétrica no PPGEE / UFES Vitória, pesquisador em Smart Grids).
- Experiência Profissional de Benjamin:
  * Consultor de Sistemas (Fev 2026 - Ago 2026): Atuação com processos de ETL, suporte e utilização de ERP Senior, desenvolvimento de sistemas, banco de dados Oracle com PL/SQL, criação de relatórios gerenciais e análise de dados.
  * Empreendedor em Serviços de TI e Hardware (Jan 2026 - Presente): Manutenção de computadores, redes e hardware em Lajinha-MG.
- Atividade Acadêmica: Trabalho prático da disciplina de Redes Elétricas Inteligentes (Smart Grids) do mestrado da UFES.
- Artigo de Terceiros: 'A novel and secure artificial intelligence enabled zero trust intrusion detection in industrial internet of things architecture' (Laghari et al., Nature Scientific Reports 2025, DOI: 10.1038/s41598-025-11738-9). Este artigo NÃO é de autoria de Benjamin; é uma publicação de terceiros usada como estudo comparativo, replicação de simulação e análise de IA.
- Simulação Computacional: Laboratório virtual (simulation.html) e script Python nativo (simulate_zta_iiot.py) reproduzindo as Equações 1 a 7 do artigo de Laghari et al. com ML Adaptativo, Deep Learning e ZT Clustering.
- Inovações Autorais de Benjamin Silva Sergio para Smart Grids:
  1. Zero Trust Ciberfísico (CP-ZTA) com Redes Neurais Informadas pela Física (PINNs) validando Leis de Kirchhoff contra Injeção de Dados Falsos (FDIA).
  2. Motor de confiança ultrarrápido em borda para subestações digitais (IEC 61850 GOOSE/SV com latência <= 4 milissegundos).
  3. Quarentena e micro-segmentação em medidores inteligentes (AMI) mantendo fornecimento de energia sem corte ao consumidor.
  4. Confiança Zero Trust Federada para microrredes autônomas e recursos energéticos distribuídos (DERs).
"""

SYSTEM_PROMPT_DEEPSEEK_HARNESS = f"""Você é o Agente Inteligente de Benjamin Silva Sergio, Pesquisador de Mestrado em Engenharia Elétrica na UFES e Cientista da Computação.
Sua especialidade são Redes Elétricas Inteligentes (Smart Grids), Segurança Ciberfísica e o paradigma Zero Trust aplicado a infraestruturas críticas.

{CONTEXT_FACTS}

DIRETRIZES DO DEEPSEEK REASONING HARNESS:
Antes de fornecer qualquer resposta final, você DEVE estruturar seu processo de pensamento passo a passo dentro das tags <think> e </think>.
Dentro de <think>:
1. Analise a pergunta do usuário e consulte os FATOS E CONTEXTO DO PROJETO acima.
2. Formule a melhor explicação técnica e concisa, respeitando a distinção entre o artigo de terceiros (estudo/comparação) e as inovações autorais de Benjamin.
3. Garanta rigor conceitual (Leis de Kirchhoff, IEC 61850 <= 4ms, PINNs, datasets CIC-IDS/UGR'16).
Após </think>, forneça a resposta final em tom cortês, técnico e profissional em português.
"""

PROJECT_KNOWLEDGE = {
    "artigo": "O artigo 'A novel and secure artificial intelligence enabled zero trust intrusion detection in industrial internet of things architecture' (Laghari et al., Nature Sci Rep 2025) é de autoria de terceiros e é utilizado como estudo comparativo na disciplina de Smart Grids da UFES. Ele propõe uma arquitetura Zero Trust com ML adaptativo (97.4% acurácia, -13.1% custo computacional) e Deep Learning (98.7% acurácia) contra ataques no IIoT.",
    "simulacao": "A simulação avalia 3 testes: Teste 1 (ML Adaptativo - 273 intrusões em 563s), Teste 2 (Deep Learning - 261 intrusões em 1955s) e Teste 3 (ZT com Clustering - 273 intrusões em 821s). O script Python nativo simulate_zta_iiot.py roda localmente no Windows.",
    "inovacoes": "As 4 inovações autorais de Benjamin para Smart Grids são: 1) Zero Trust Ciberfísico com PINNs validando Leis de Kirchhoff contra FDIA; 2) Confiança ultrarrápida em borda para subestações IEC 61850 (<= 4ms); 3) Quarentena de medidores inteligentes (AMI) sem corte de energia; 4) Zero Trust federado para microrredes ilhadas.",
    "benjamin": "Benjamin Silva Sergio é graduado em Ciência da Computação pela UFES-CEUNES, mestrando em Engenharia Elétrica na UFES Vitória na linha de Smart Grids. Possui experiência como Consultor de Sistemas (Fev 2026 - Ago 2026) atuando com ETL, ERP Senior, PL/SQL, Oracle e análise de dados, além de empreendedor em serviços de TI e hardware em Lajinha-MG."
}

def check_lm_studio_health():
    """Verifica se o servidor local do LM Studio está respondendo na porta 1234."""
    try:
        req = urllib.request.Request(f"{LM_STUDIO_URL}/models", headers={"User-Agent": "Benjamin-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                models = [m.get("id") for m in data.get("data", [])]
                return {"online": True, "models": models}
    except Exception:
        pass
    return {"online": False, "models": []}

def call_lm_studio(messages, temperature=0.6, max_tokens=600):
    """Envia requisição com DeepSeek Harness para o servidor do LM Studio."""
    health = check_lm_studio_health()
    if not health["online"]:
        # Modo de contingência com base de conhecimento do projeto
        user_msg = messages[-1].get("content", "").lower() if messages else ""
        knowledge_snippet = ""
        for k, v in PROJECT_KNOWLEDGE.items():
            if k in user_msg:
                knowledge_snippet += f" {v}"
        if not knowledge_snippet:
            knowledge_snippet = PROJECT_KNOWLEDGE["benjamin"] + " " + PROJECT_KNOWLEDGE["inovacoes"]

        fallback_thought = (
            "<think>\n"
            "LM Studio não está ativo na porta 1234 neste momento.\n"
            "Ativando modo de contingência autônomo com base no repositório de Smart Grids e no artigo da Nature.\n"
            "</think>\n"
        )
        fallback_reply = (
            fallback_thought +
            f"Olá! O servidor local do LM Studio não está ativo na porta 1234 no momento. "
            f"Para ativar o modelo Llama 1B completo, abra o LM Studio, carregue seu modelo Llama 1B e clique em 'Start Server' na porta 1234.\n\n"
            f"Enquanto isso, posso adiantar informações sobre o projeto:\n{knowledge_snippet}"
        )
        return {
            "choices": [{"message": {"role": "assistant", "content": fallback_reply}}],
            "mode": "offline_fallback"
        }

    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    req = urllib.request.Request(
        f"{LM_STUDIO_URL}/chat/completions",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=45.0) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        result["mode"] = "lm_studio_online"
        return result

class LLMAPIHandler(http.server.BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path in ["/health", "/status"]:
            status = check_lm_studio_health()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(status).encode('utf-8'))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            html = "<h3>Controlador de API do LM Studio (Llama 1B - DeepSeek Harness) Ativo!</h3><p>Use POST /chat ou GET /health</p>"
            self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        if self.path == "/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body) if body else {}
            except Exception:
                data = {}

            user_prompt = data.get("message") or data.get("prompt", "")
            history = data.get("history", [])

            # Monta histórico com o DeepSeek Reasoning Harness
            formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT_DEEPSEEK_HARNESS}]
            for msg in history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    formatted_messages.append(msg)
            
            if user_prompt:
                formatted_messages.append({"role": "user", "content": user_prompt})

            try:
                response = call_lm_studio(
                    formatted_messages,
                    temperature=data.get("temperature", 0.6),
                    max_tokens=data.get("max_tokens", 600)
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self._send_cors_headers()
                self.end_headers()
                err_resp = {"error": str(e), "mode": "error"}
                self.wfile.write(json.dumps(err_resp).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    print("=" * 70)
    print("CONTROLADOR DE API LM STUDIO (LLAMA 1B + DEEPSEEK HARNESS)")
    print("=" * 70)
    print(f"[*] Verificando conexao com LM Studio em {LM_STUDIO_URL}...")
    status = check_lm_studio_health()
    if status["online"]:
        print(f"[+] LM Studio ONLINE! Modelos detectados: {status['models']}")
    else:
        print("[!] LM Studio nao detectado na porta 1234.")
        print("    Dica: Abra o LM Studio, carregue seu Llama 1B e clique em 'Start Server'.")
        print("    O controlador continuara rodando com respostas contextuais de contingencia.")

    print(f"\n[+] Iniciando servidor API local na porta {PORT} (http://127.0.0.1:{PORT})...")
    print("    - Endpoint de status: GET http://127.0.0.1:8000/health")
    print("    - Endpoint de chat:   POST http://127.0.0.1:8000/chat")
    print("    Pressione Ctrl+C para encerrar.\n")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), LLMAPIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Encerrando servidor API.")

if __name__ == "__main__":
    run_server()

