"""
Consumidor e Agente Autônomo com DeepSeek Reasoning Harness
Autor: Benjamin Silva Sergio (UFES / Smart Grids)

Este script consome a API do Llama 1B (via llm_api_controller.py ou diretamente LM Studio),
operando o LLM através do DeepSeek Harness (raciocínio passo a passo com <think> e resposta final).

Uso:
    python llm_agent_consumer.py                  # Modo conversa interativa no terminal
    python llm_agent_consumer.py --test           # Teste rápido de conectividade e raciocínio
    python llm_agent_consumer.py --prompt "texto" # Pergunta direta
"""

import sys
import json
import urllib.request
import urllib.error
import re
import argparse

API_URL = "http://127.0.0.1:8000/chat"
DIRECT_LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"

def query_agent(prompt, history=None):
    """Envia requisição para a API controladora com fallback direto."""
    payload = {
        "message": prompt,
        "history": history or [],
        "temperature": 0.6,
        "max_tokens": 700
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data
    except urllib.error.URLError:
        # Se o controlador na porta 8000 estiver desligado, tenta falar com o LM Studio direto
        try:
            lm_payload = {
                "messages": [
                    {"role": "system", "content": "Você é o agente inteligente de Benjamin Silva Sergio para a disciplina de mestrado em Smart Grids (UFES). O artigo da Nature é de terceiros (usado como comparação) e as inovações são autorais de Benjamin. Raciocine dentro de <think>...</think> antes de responder."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.6,
                "max_tokens": 600
            }
            lm_req = urllib.request.Request(
                DIRECT_LM_STUDIO_URL,
                data=json.dumps(lm_payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(lm_req, timeout=30.0) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                data["mode"] = "direct_lm_studio"
                return data
        except Exception:
            return {
                "error": "Não foi possível conectar nem ao controlador (porta 8000) nem ao LM Studio (porta 1234). Inicie 'python llm_api_controller.py' ou inicie o servidor no aplicativo LM Studio."
            }

def parse_deepseek_reasoning(content):
    """Extrai e formata o bloco de pensamento <think> e a resposta final."""
    think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL | re.IGNORECASE)
    if think_match:
        thought = think_match.group(1).strip()
        answer = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        return thought, answer
    return None, content.strip()

def display_response(resp_data):
    if "error" in resp_data:
        print(f"\n[ERRO] {resp_data['error']}\n")
        return

    choices = resp_data.get("choices", [])
    if not choices:
        print("\n[AVISO] Nenhuma resposta retornada pelo modelo.")
        return

    raw_text = choices[0].get("message", {}).get("content", "")
    thought, answer = parse_deepseek_reasoning(raw_text)

    print("\n" + "=" * 70)
    if thought:
        print("[DEEPSEEK HARNESS - PROCESSO DE RACIOCINIO / THINKING]:")
        print("-" * 70)
        print(thought)
        print("-" * 70)

    print("[RESPOSTA DO AGENTE LLAMA 1B]:")
    print("-" * 70)
    print(answer)
    print("=" * 70 + "\n")

def interactive_loop():
    print("=" * 70)
    print("AGENTE AUTÔNOMO LLAMA 1B (DEEPSEEK REASONING HARNESS)")
    print("Pesquisa em Smart Grids - Benjamin Silva Sergio (UFES)")
    print("=" * 70)
    print("Digite sua pergunta abaixo (ou 'sair' / 'exit' para encerrar):\n")

    history = []
    while True:
        try:
            user_input = input("Você > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["sair", "exit", "quit"]:
                print("Até logo!")
                break

            print("\n[*] Agente pensando e processando resposta com Llama 1B...")
            resp = query_agent(user_input, history)
            display_response(resp)

            if "choices" in resp and resp["choices"]:
                reply_text = resp["choices"][0].get("message", {}).get("content", "")
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": reply_text})

        except KeyboardInterrupt:
            print("\nEncerrando sessão.")
            break

def main():
    parser = argparse.ArgumentParser(description="Consumidor do Llama 1B com DeepSeek Harness")
    parser.add_argument("--test", action="store_true", help="Executa teste rápido de diagnóstico")
    parser.add_argument("--prompt", type=str, help="Envia pergunta única diretamente")

    args = parser.parse_args()

    if args.test:
        print("[*] Executando teste de diagnóstico de integração...")
        test_prompt = "Explique em duas frases as inovações de Benjamin Silva Sergio para Smart Grids com Zero Trust."
        print(f"Prompt de teste: '{test_prompt}'")
        resp = query_agent(test_prompt)
        display_response(resp)
    elif args.prompt:
        resp = query_agent(args.prompt)
        display_response(resp)
    else:
        interactive_loop()

if __name__ == "__main__":
    main()
