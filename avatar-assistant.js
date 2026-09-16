/**
 * Assistente Mii Flutuante + Chat com IA (Llama 1B • DeepSeek Harness)
 * Criado para o portfólio de Benjamin Silva Sergio (UFES / Smart Grids)
 * 
 * Funcionalidades:
 * - Botão flutuante do avatar Mii no canto da tela com narração por voz (Web Speech API).
 * - Botão de Chat (💬) adjacente que abre o console de conversa direta com a IA.
 * - Integração com o controlador local (http://127.0.0.1:8000/chat) e LM Studio (Llama 1B).
 * - Renderização do processo de raciocínio passo a passo do DeepSeek Harness (<think>...</think>).
 * - Modo inteligente de contingência/fallback quando o servidor local ainda não foi iniciado.
 */

(function() {
    const API_URL = "http://127.0.0.1:8000/chat";
    const HEALTH_URL = "http://127.0.0.1:8000/health";

    const pageNarrations = {
        'index': {
            title: 'Início • Portfólio & Atividade Acadêmica',
            badge: 'Mestrado Smart Grids',
            text: 'Olá! Eu sou o avatar de Benjamin Silva Sergio. Este portal foi desenvolvido como atividade prática da disciplina de Smart Grids no mestrado da UFES. O artigo da Nature analisado aqui é de autoria de terceiros e serve como objeto de estudo e comparação. A partir dele, desenvolvemos o laboratório de simulação e propostas autorais de inovação com Inteligência Artificial para redes elétricas inteligentes. Fique à vontade para explorar os botões no topo ou clicar nas seções abaixo!'
        },
        'article': {
            title: 'Artigo Científico • Nature Portfolio',
            badge: 'Artigo Internacional',
            text: 'Você está na página de análise do artigo científico da Nature Scientific Reports, publicado em 2025 por Laghari e equipe. O estudo comprova que a arquitetura Zero Trust, baseada no princípio Nunca Confie, Sempre Verifique, reduz os custos computacionais em 13,1% e atinge até 98,7% de eficiência contra intrusões de rede. Aqui você confere o resumo executivo, as formulações matemáticas das equações de 1 a 7 e as tabelas comparativas!'
        },
        'simulation': {
            title: 'Laboratório Virtual • Simulação Interativa',
            badge: 'Simulação em Tempo Real',
            text: 'Bem-vindo ao Laboratório Virtual de Simulação! Aqui você pode testar e comparar os modelos empíricos do artigo. Selecione entre Aprendizado de Máquina Adaptativo, Deep Learning ou Zero Trust com Clustering, ajuste o volume de pacotes e a taxa de injeção de ataques nos controles, e clique em Iniciar Simulação para ver as curvas de detecção e o consumo computacional. Você também pode rodar o script Python localmente!'
        },
        'innovation': {
            title: 'Inovações Autorais • Smart Grids (UFES)',
            badge: 'Proposta Autoral',
            text: 'Esta é a página de inovações autorais desenvolvidas pelo Benjamin para Redes Elétricas Inteligentes. Aqui o modelo Zero Trust tradicional é expandido para a física da rede: usamos redes neurais guiadas pelas Leis de Kirchhoff para detectar injeção de dados falsos, criamos um motor de confiança ultrarrápido para subestações digitais na norma IEC 61850 com latência menor que 4 milissegundos, isolamento de medidores inteligentes sem cortar a energia do cliente e proteção federada para microrredes!'
        }
    };

    const FALLBACK_KNOWLEDGE = {
        artigo: "O artigo 'A novel and secure artificial intelligence enabled zero trust intrusion detection in industrial internet of things architecture' (Laghari et al., Nature Sci Rep 2025) propõe arquitetura Zero Trust com ML adaptativo (97.4% acurácia, -13.1% custo computacional) e Deep Learning (98.7% acurácia) testados com os datasets CIC-IDS e UGR'16.",
        simulacao: "A simulação compara 3 testes: ML Adaptativo (273 intrusões em 563s), Deep Learning (261 em 1955s) e ZT com Clustering (273 em 821s). O script Python nativo simulate_zta_iiot.py executa as Equações 1 a 7 sem dependências externas.",
        inovacao: "As 4 inovações autorais de Benjamin Silva Sergio para Smart Grids são: 1) Zero Trust Ciberfísico com PINNs validando Leis de Kirchhoff contra FDIA; 2) Avaliação em borda para subestações IEC 61850 (latência <= 4ms); 3) Quarentena de medidores inteligentes (AMI) sem corte de energia; 4) Zero Trust federado em microrredes.",
        benjamin: "Benjamin Silva Sergio é graduado em Ciência da Computação pela UFES-CEUNES e mestrando em Engenharia Elétrica na UFES Vitória, pesquisando Smart Grids. Atuou como Consultor de Sistemas (Fev-Ago 2026) com ETL, ERP Senior, PL/SQL, Oracle e análise de dados, além de serviços em TI e hardware."
    };

    function getCurrentPageKey() {
        const path = window.location.pathname.toLowerCase();
        if (path.includes('article')) return 'article';
        if (path.includes('simulation')) return 'simulation';
        if (path.includes('innovation')) return 'innovation';
        return 'index';
    }

    function initAssistantAndChat() {
        const pageKey = getCurrentPageKey();
        const pageData = pageNarrations[pageKey] || pageNarrations['index'];

        // Cria o contêiner flutuante no DOM
        const widget = document.createElement('div');
        widget.className = 'floating-avatar-widget';
        widget.id = 'floatingAvatarWidget';

        widget.innerHTML = `
            <!-- Janela de Chat com a IA -->
            <div class="mii-chat-drawer" id="miiChatDrawer" style="display: none;">
                <div class="chat-header">
                    <div class="chat-header-title">
                        <strong>🤖 Agente IA • Llama 1B</strong>
                        <div class="chat-status-text">
                            <span class="chat-status-indicator offline" id="chatStatusDot"></span>
                            <span id="chatStatusText">Verificando LM Studio...</span>
                        </div>
                    </div>
                    <button class="chat-close-btn" id="chatCloseBtn" title="Fechar chat">&times;</button>
                </div>

                <!-- Chips de Perguntas Rápidas -->
                <div class="chat-chips-bar">
                    <button class="chat-chip" onclick="window.sendPredefinedPrompt('Explique o artigo da Nature')">📄 Artigo Nature</button>
                    <button class="chat-chip" onclick="window.sendPredefinedPrompt('Como funciona a simulação?')">🧪 Simulação</button>
                    <button class="chat-chip" onclick="window.sendPredefinedPrompt('Quais as inovações em Smart Grids?')">💡 Inovações</button>
                    <button class="chat-chip" onclick="window.sendPredefinedPrompt('Quem é Benjamin Silva Sergio?')">👤 Autor</button>
                </div>

                <!-- Histórico de Mensagens -->
                <div class="chat-messages" id="chatMessages">
                    <div class="chat-msg agent">
                        Olá! Eu sou o agente autônomo baseado no <strong>Llama 1B</strong> com scaffolding <strong>DeepSeek Harness</strong>.
                        Como posso te ajudar sobre a pesquisa de Smart Grids, o artigo da Nature ou as simulações de Zero Trust?
                    </div>
                </div>

                <!-- Campo de Entrada -->
                <div class="chat-input-area">
                    <input type="text" class="chat-input" id="chatInput" placeholder="Pergunte ao Llama 1B..." autocomplete="off">
                    <button class="chat-send-btn" id="chatSendBtn" title="Enviar mensagem">➤</button>
                </div>
            </div>

            <!-- Balão de Fala do Avatar Mii -->
            <div class="mii-speech-bubble" id="miiBubble" style="display: none;">
                <div class="mii-speech-bubble-header">
                    <span class="mii-badge">${pageData.badge}</span>
                    <button class="mii-close-btn" id="miiCloseBtn" title="Fechar balão">&times;</button>
                </div>
                <div class="mii-speech-text" id="miiSpeechText">
                    <strong>${pageData.title}:</strong><br>
                    ${pageData.text}
                </div>
                <div class="mii-bubble-actions">
                    <button class="mii-btn" id="miiSpeakBtn">
                        <span id="miiBtnIcon">🔊</span> <span id="miiBtnLabel">Ouvir Explicação</span>
                    </button>
                    <button class="mii-btn stop" id="miiStopBtn" style="display: none;">
                        ⏹️ Parar
                    </button>
                </div>
            </div>

            <!-- Linha de Botões (Chat + Avatar) -->
            <div class="mii-buttons-row">
                <div class="mii-chat-toggle-btn" id="miiChatToggleBtn" title="Abrir Chat com Agente IA (Llama 1B)">
                    💬
                    <span class="mii-chat-status-dot offline" id="btnStatusDot"></span>
                </div>

                <div class="mii-avatar-btn" id="miiAvatarBtn" title="Clique para interagir comigo sobre esta página!">
                    <img src="avatar.png" alt="Avatar Nintendo Wii Mii de Benjamin" id="miiAvatarImg">
                    <div class="mii-mic-status" id="miiMicStatus">🎙️</div>
                </div>
            </div>
        `;

        document.body.appendChild(widget);

        // Referências
        const avatarBtn = document.getElementById('miiAvatarBtn');
        const bubble = document.getElementById('miiBubble');
        const closeBtn = document.getElementById('miiCloseBtn');
        const speakBtn = document.getElementById('miiSpeakBtn');
        const stopBtn = document.getElementById('miiStopBtn');
        const btnIcon = document.getElementById('miiBtnIcon');
        const btnLabel = document.getElementById('miiBtnLabel');

        const chatToggleBtn = document.getElementById('miiChatToggleBtn');
        const chatDrawer = document.getElementById('miiChatDrawer');
        const chatCloseBtn = document.getElementById('chatCloseBtn');
        const chatInput = document.getElementById('chatInput');
        const chatSendBtn = document.getElementById('chatSendBtn');
        const chatMessages = document.getElementById('chatMessages');
        const chatStatusDot = document.getElementById('chatStatusDot');
        const btnStatusDot = document.getElementById('btnStatusDot');
        const chatStatusText = document.getElementById('chatStatusText');

        let isLMStudioOnline = false;
        let chatHistory = [];

        // =========================================================
        // VERIFICAÇÃO DE STATUS DA API / LM STUDIO
        // =========================================================
        async function checkStatus() {
            try {
                const res = await fetch(HEALTH_URL, { method: 'GET', mode: 'cors' });
                if (res.ok) {
                    const data = await res.json();
                    if (data.online) {
                        isLMStudioOnline = true;
                        chatStatusDot.className = 'chat-status-indicator online';
                        btnStatusDot.className = 'mii-chat-status-dot';
                        chatStatusText.innerText = `Llama 1B Online (${data.models[0] || 'LM Studio'})`;
                        return;
                    }
                }
            } catch (e) {
                // API Controller ainda não iniciado
            }

            isLMStudioOnline = false;
            chatStatusDot.className = 'chat-status-indicator offline';
            btnStatusDot.className = 'mii-chat-status-dot offline';
            chatStatusText.innerText = 'LM Studio Offline (Porta 1234)';
        }

        checkStatus();
        setInterval(checkStatus, 8000); // Polling a cada 8s

        // =========================================================
        // CONTROLE DE SÍNTESE DE VOZ DO AVATAR MII
        // =========================================================
        const synth = window.speechSynthesis;
        let isSpeaking = false;

        function stopSpeaking() {
            if (synth) synth.cancel();
            isSpeaking = false;
            avatarBtn.classList.remove('speaking');
            speakBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
            btnIcon.innerText = '🔊';
            btnLabel.innerText = 'Ouvir Novamente';
            document.getElementById('miiMicStatus').innerText = '🎙️';

            const headerWrapper = document.getElementById('avatarWrapper');
            const headerSpeechBtn = document.getElementById('speechBtn');
            if (headerWrapper) headerWrapper.classList.remove('speaking');
            if (headerSpeechBtn) {
                headerSpeechBtn.classList.remove('active');
                const label = document.getElementById('speechTextLabel');
                const icon = document.getElementById('speechIcon');
                if (label) label.innerText = 'Ouvir Apresentação em Voz';
                if (icon) icon.innerText = '🎙️';
            }
        }

        function startSpeaking() {
            if (!synth) {
                alert('Seu navegador não possui suporte à síntese de voz (Web Speech API).');
                return;
            }

            stopSpeaking();

            const utterance = new SpeechSynthesisUtterance(pageData.text);
            utterance.lang = 'pt-BR';
            utterance.rate = 1.06;
            utterance.pitch = 1.0;

            const voices = synth.getVoices();
            const ptVoice = voices.find(v => v.lang === 'pt-BR' || v.lang.startsWith('pt'));
            if (ptVoice) {
                utterance.voice = ptVoice;
            }

            utterance.onstart = function() {
                isSpeaking = true;
                avatarBtn.classList.add('speaking');
                speakBtn.style.display = 'none';
                stopBtn.style.display = 'inline-flex';
                document.getElementById('miiMicStatus').innerText = '🔊';

                const headerWrapper = document.getElementById('avatarWrapper');
                const headerSpeechBtn = document.getElementById('speechBtn');
                if (headerWrapper) headerWrapper.classList.add('speaking');
                if (headerSpeechBtn) {
                    headerSpeechBtn.classList.add('active');
                    const label = document.getElementById('speechTextLabel');
                    const icon = document.getElementById('speechIcon');
                    if (label) label.innerText = 'Parar Leitura';
                    if (icon) icon.innerText = '⏹️';
                }
            };

            utterance.onend = stopSpeaking;
            utterance.onerror = stopSpeaking;

            synth.speak(utterance);
        }

        function toggleBubbleAndSpeech() {
            chatDrawer.style.display = 'none'; // Fecha chat se abrir o balão
            if (bubble.style.display === 'none') {
                bubble.style.display = 'block';
                startSpeaking();
            } else {
                if (isSpeaking) stopSpeaking();
                else startSpeaking();
            }
        }

        window.toggleMiiAssistant = toggleBubbleAndSpeech;

        avatarBtn.addEventListener('click', toggleBubbleAndSpeech);
        closeBtn.addEventListener('click', () => { bubble.style.display = 'none'; stopSpeaking(); });
        speakBtn.addEventListener('click', (e) => { e.stopPropagation(); startSpeaking(); });
        stopBtn.addEventListener('click', (e) => { e.stopPropagation(); stopSpeaking(); });

        // =========================================================
        // CONTROLE DO CHAT COM IA (LLAMA 1B + DEEPSEEK HARNESS)
        // =========================================================
        function toggleChat() {
            bubble.style.display = 'none'; // Fecha balão de fala se abrir chat
            stopSpeaking();
            if (chatDrawer.style.display === 'none') {
                chatDrawer.style.display = 'flex';
                chatInput.focus();
            } else {
                chatDrawer.style.display = 'none';
            }
        }

        chatToggleBtn.addEventListener('click', toggleChat);
        chatCloseBtn.addEventListener('click', () => { chatDrawer.style.display = 'none'; });

        function appendMessage(sender, text, reasoning = null) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `chat-msg ${sender}`;

            let html = '';
            if (reasoning) {
                html += `
                    <details class="think-accordion" open>
                        <summary>🧠 Raciocínio (DeepSeek Harness)</summary>
                        <pre>${escapeHtml(reasoning)}</pre>
                    </details>
                `;
            }
            html += formatMarkdown(text);
            msgDiv.innerHTML = html;
            chatMessages.appendChild(msgDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function escapeHtml(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        function formatMarkdown(text) {
            // Formatação leve de negrito, listas e quebras de linha
            let formatted = escapeHtml(text);
            formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
            formatted = formatted.replace(/\n/g, '<br>');
            return formatted;
        }

        function parseDeepSeekResponse(content) {
            const match = content.match(/<think>([\s\S]*?)<\/think>/i);
            if (match) {
                const thought = match[1].trim();
                const answer = content.replace(/<think>[\s\S]*?<\/think>/i, '').trim();
                return { thought, answer };
            }
            return { thought: null, answer: content.trim() };
        }

        async function sendMessage(text) {
            const query = text || chatInput.value.trim();
            if (!query) return;

            appendMessage('user', query);
            chatInput.value = '';
            chatSendBtn.disabled = true;

            // Placeholder de carregamento
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'chat-msg agent';
            loadingDiv.id = 'loadingMsg';
            loadingDiv.innerHTML = '<em>Agente raciocinando com Llama 1B...</em>';
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const res = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: query,
                        history: chatHistory
                    })
                });

                if (loadingDiv) loadingDiv.remove();

                if (res.ok) {
                    const data = await res.json();
                    const rawContent = data.choices && data.choices[0] ? data.choices[0].message.content : '';
                    const parsed = parseDeepSeekResponse(rawContent);

                    appendMessage('agent', parsed.answer, parsed.thought);
                    chatHistory.push({ role: 'user', content: query });
                    chatHistory.push({ role: 'assistant', content: rawContent });
                } else {
                    throw new Error('Servidor retornou erro HTTP ' + res.status);
                }
            } catch (err) {
                if (loadingDiv) loadingDiv.remove();

                // Modo contingência inteligente local
                let answerText = "";
                let lower = query.toLowerCase();
                if (lower.includes("artigo") || lower.includes("nature") || lower.includes("laghari")) {
                    answerText = FALLBACK_KNOWLEDGE.artigo;
                } else if (lower.includes("simula") || lower.includes("teste")) {
                    answerText = FALLBACK_KNOWLEDGE.simulacao;
                } else if (lower.includes("inova") || lower.includes("pinn") || lower.includes("kirchhoff")) {
                    answerText = FALLBACK_KNOWLEDGE.inovacao;
                } else {
                    answerText = `${FALLBACK_KNOWLEDGE.benjamin} ${FALLBACK_KNOWLEDGE.inovacao}`;
                }

                const fallbackThought = "Controlador local (porta 8000) ou LM Studio (porta 1234) offline.\nGerando resposta contextual autônoma a partir da base do projeto de Smart Grids.";
                const fallbackMessage = answerText + "\n\n*(Dica: Para conectar com o Llama 1B real, execute 'python llm_api_controller.py' no terminal e inicie o servidor no LM Studio!)*";

                appendMessage('agent', fallbackMessage, fallbackThought);
            } finally {
                chatSendBtn.disabled = false;
            }
        }

        chatSendBtn.addEventListener('click', () => sendMessage());
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        window.sendPredefinedPrompt = function(promptText) {
            sendMessage(promptText);
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAssistantAndChat);
    } else {
        initAssistantAndChat();
    }
})();
