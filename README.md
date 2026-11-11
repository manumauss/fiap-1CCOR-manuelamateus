# Missão Aurora Siger (Fase 3) — SIGPC: Sistema Inteligente de Gestão e Previsão da Colônia

**Aluna:** Manuela Mateus — RM 576139  
**Turma:** 1CCOR — Ciência da Computação (FIAP)  
**Repositório (branch `fase-3`):** https://github.com/manumauss/fiap-1CCOR-manuelamateus/tree/fase-3

Sistema integrado da Fase 3 da missão Aurora Siger (colônia em Marte). Em Python puro, organizado em funções, ele:

1. **organiza os dados da colônia** em uma árvore de subsistemas (energético → solar / eólico / bateria; ambiental; operacional) feita com dicionários e listas;
2. **prevê a geração eólica** a partir do vento com regressão linear simples (mínimos quadrados);
3. **toma decisões automáticas** com regras booleanas, priorizando o suporte à vida;
4. **analisa o uso de energia**, comparando geração, consumo e reserva de bateria.

---

## Arquivos do repositório

| Arquivo | Conteúdo |
|---|---|
| `sigpc_colonia.py` | Código-fonte completo, em funções, separado em blocos: dados, previsão, decisões, análise de energia, exibição e programa principal. Sem bibliotecas externas. |
| `Relatorio_Tecnico_Fase3_Colonia_Aurora_Siger.pdf` | Relatório técnico: organização dos dados, regras de decisão, modelo de previsão e como o sistema melhora o uso de energia. |
| `README.md` | Este arquivo: funcionamento, execução e exemplos de entrada e saída. |

---

## Como executar

Requisito: Python 3 (testado em 3.13). Nenhuma biblioteca externa precisa ser instalada.

```bash
git clone -b fase-3 https://github.com/manumauss/fiap-1CCOR-manuelamateus.git
cd fiap-1CCOR-manuelamateus
python sigpc_colonia.py
```

---

## Como o sistema funciona

O arquivo `sigpc_colonia.py` segue o fluxo **entrada → processamento → saída** em seis blocos:

### 1. Dados — `inicializar_colonia()`, `exibir_hierarquia()`, `consultar_subsistema_recursivo()`
- Os dados ficam em uma **árvore de dicionários** (tabela chave-valor, acesso direto pela chave):  
  `colonia["energetico"]["solar"]`, `colonia["energetico"]["eolico"]`, `colonia["energetico"]["bateria"]`, `colonia["ambiental"]["clima_atual"]`, `colonia["operacional"]["modulos"]`.
- As **séries históricas** são listas: a calibração do enunciado (`historico_vento = [8.0, 10.0, 12.0]`, `historico_energia_eolica = [20.0, 25.0, 30.0]`) e oito leituras de campo em `leituras_campo` (vento medido e geração medida).
- `exibir_hierarquia()` percorre a árvore recursivamente e mostra os níveis; `consultar_subsistema_recursivo()` navega até uma chave (ex.: `"clima_atual"`).

### 2. Previsão — `ajustar_regressao_linear()`, `calcular_residuos()`, `prever_energia_eolica()`
- Ajusta a reta `energia = β0 + β1 · vento` pelo método dos mínimos quadrados e calcula o R².
- Com os dados do enunciado a reta é `energia = 0,00 + 2,50 · vento` (R² = 1,00). Para `vento = 11` a previsão é **27,5 kW** (o enunciado indica ≈ 27).
- O modelo é validado com as 8 leituras de campo: reta `energia = −0,72 + 2,57 · vento`, **R² = 0,98**, resíduos entre −1,7 e +1,5 kW sem padrão. As duas retas quase coincidem e ambas estimam 27,5 kW para 11 m/s.
- A reta é uma aproximação local: a potência do vento cresce com o cubo da velocidade, então o modelo só vale na faixa das leituras (5 a 16 m/s). Fora da faixa de operação da turbina (vento abaixo do *cut-in* de 3 m/s ou acima do *cut-out* de 25 m/s) a previsão é 0 kW.

### 3. Decisão — `tomar_decisao_automatica()`, `aplicar_priorizacao_modulos()`
Três variáveis booleanas: **E** = energia < 50 (bateria baixa), **C** = consumo ≥ 60 (consumo alto), **P** = previsão eólica < 25 kW (previsão desfavorável). As regras são avaliadas em ordem de prioridade:

| Nível | Condição | Saída | Ação |
|---|---|---|---|
| 1 | E **e** C | `ALERTA: reduzir consumo` | Modo economia: mantém Suporte à Vida, Médico e Comunicação; desliga Laboratório e Mineração. |
| 2 | E **e não** C | `ALERTA: reduzir consumo` | Alerta preventivo: não ativa novas cargas. |
| 3 | **não** E **e** C **e** P | `ATENCAO: preparar reserva de energia` | Risco preditivo: adia cargas não essenciais. |
| 4 | caso contrário | `NORMAL: sistemas estabilizados` | Operação nominal. |

A regra "reduzir consumo" dispara sempre que E = 1: pela tabela-verdade, X = E·C' + E·C = E·(C' + C) = E. O C só muda a severidade (nível 1 corta cargas, nível 2 apenas alerta).

### 4. Análise de energia — `analisar_uso_energia()`
- `consumo > geracao` → `ALERTA: consumo maior que geração` (a recomendação muda conforme a reserva da bateria);
- `geracao > consumo` → `SUGESTÃO: armazenar energia excedente`;
- iguais → `EQUILIBRIO: geração igual ao consumo`.

### 5. Simulação — `simular_matriz_cenarios()`
Uma **matriz 2D** (lista de listas) com 4 ciclos `[ciclo, vento, solar, consumo, bateria]`. Para cada linha o sistema prevê a eólica, decide e analisa o balanço. Os 4 ciclos foram escolhidos para acionar cada um dos 4 níveis de decisão.

### 6. Programa principal — `executar_sigpc()`
Encadeia tudo: previsão eólica → decisão → corte de cargas → balanço integrado → simulação.

---

## Exemplos de entrada e saída

Os exemplos abaixo são trechos reais da execução de `python sigpc_colonia.py`.

### Previsão de energia eólica (regressão linear)
**Entrada:** `vento = [8, 10, 12]`, `energia = [20, 25, 30]`, leitura atual `vento = 11`

```text
Reta Ajustada (MMQ)  : Energia = 0.00 + 2.50 * Vento  (R^2 = 1.00)
Entrada              : vento = 11
Saida                : previsao de energia = 27.5 kW
```

**Validação com leituras de campo** (8 sols, pontos não alinhados):

```text
Vento medido (m/s)   : [5.0, 6.5, 8.0, 9.5, 11.0, 12.5, 14.0, 16.0]
Eolica medida (kW)   : [11.0, 17.5, 19.0, 25.0, 26.5, 32.5, 33.5, 41.0]
Reta Ajustada (MMQ)  : Energia = -0.72 + 2.57 * Vento  (R^2 = 0.98)
Previsao p/ vento=11 : 27.5 kW pela reta de campo | 27.5 kW pela reta de calibracao
```

### Tomada de decisão automática
**Entrada:** `energia = 40`, `consumo = 70` (e previsão eólica = 27,5 kW)

```text
Variaveis Booleanas  : E = 1 (energia < 50) | C = 1 (consumo >= 60) | P = 0 (previsao < 25)
Saida                : "ALERTA: reduzir consumo"
Modo Acionado        : MODO ECONOMIA
Priorizacao          : Manter suporte a vida ligado e desligar sistemas nao essenciais (Laboratorio Cientifico e Mineracao).
Consumo apos corte   : reduzido de 70.0 kW para 55.0 kW
```

### Análise do uso de energia
**Entrada:** `geracao = 40`, `consumo = 70` → **Saída:** `"ALERTA: consumo maior que geração"`  
**Entrada:** `geracao = 80`, `consumo = 30` → **Saída:** `"SUGESTÃO: armazenar energia excedente"`

### Simulação de 4 ciclos (matriz 2D) — cada ciclo aciona um nível de decisão

```text
CICLO | VENTO | SOLAR | EOLICA(PREV) | GER.TOTAL | CONSUMO | BAT% | E C P | DECISAO
  1   |   8.0 |  20.0 |     20.0     |    40.0   |   70.0  |   40 | 1 1 1 | ALERTA: reduzir consumo
  2   |  11.0 |  45.0 |     27.5     |    72.5   |   55.0  |   45 | 1 0 0 | ALERTA: reduzir consumo
  3   |   9.0 |  35.0 |     22.5     |    57.5   |   65.0  |   70 | 0 1 1 | ATENCAO: preparar reserva de energia
  4   |  12.0 |  50.0 |     30.0     |    80.0   |   30.0  |   85 | 0 0 0 | NORMAL: sistemas estabilizados
```

<details>
<summary><strong>Saída completa da execução</strong></summary>

```text
============================================================================
  SIGPC - SISTEMA INTELIGENTE DA COLONIA AURORA SIGER (FASE 3)
============================================================================
  Colonia Inicializada : Base Aurora Siger - Marte
  Modo de Operacao     : Off-Grid Autonomo
  Arvore de subsistemas (raiz -> subsistema -> componente -> dado):
  +-- nome = Base Aurora Siger - Marte
  +-- energetico
      +-- solar
          +-- geracao_atual = 45.0
          +-- capacidade_maxima = 100.0
          +-- tipo_celula = Silicio Monocristalino
          +-- status = OPERACIONAL
      +-- eolico
          +-- geracao_atual = 25.0
          +-- capacidade_maxima = 80.0
          +-- tipo_turbina = Horizontal (HAWT)
          +-- cut_in_ms = 3.0
          +-- cut_out_ms = 25.0
          +-- status = OPERACIONAL
      +-- bateria
          +-- energia_pct = 40.0
          +-- capacidade_kwh = 2000.0
          +-- modo_sistema = Off-Grid Autonomo
  +-- ambiental
      +-- clima_atual
          +-- vento_ms = 11.0
          +-- irradiancia_wm2 = 520.0
          +-- temp_interna_c = 22.0
          +-- temp_externa_c = -55.0
      +-- historico_vento: lista com 3 itens
      +-- historico_energia_eolica: lista com 3 itens
      +-- leituras_campo
          +-- vento: lista com 8 itens
          +-- energia_eolica: lista com 8 itens
  +-- operacional
      +-- consumo_atual = 70.0
      +-- modulos: lista com 5 itens

  Busca recursiva 'clima_atual' -> Vento = 11.0 m/s | Irradiancia = 520.0 W/m2 | Temp. Externa = -55.0 C

============================================================================
  1. PREVISAO DE GERACAO EOLICA (REGRESSAO LINEAR SIMPLES)
============================================================================
  Dados Historicos     : vento = [8.0, 10.0, 12.0] m/s | energia = [20.0, 25.0, 30.0] kW
  Reta Ajustada (MMQ)  : Energia = 0.00 + 2.50 * Vento  (R^2 = 1.00)
  Entrada              : vento = 11
  Saida                : previsao de energia = 27.5 kW

  [Validacao do modelo com 8 leituras de campo]
  Vento medido (m/s)   : [5.0, 6.5, 8.0, 9.5, 11.0, 12.5, 14.0, 16.0]
  Eolica medida (kW)   : [11.0, 17.5, 19.0, 25.0, 26.5, 32.5, 33.5, 41.0]
  Reta Ajustada (MMQ)  : Energia = -0.72 + 2.57 * Vento  (R^2 = 0.98)
  Residuos (e = y - y_prev):
      vento |  medido | previsto | residuo
        5.0 |   11.0  |   12.1   |   -1.1
        6.5 |   17.5  |   16.0   |   +1.5
        8.0 |   19.0  |   19.8   |   -0.8
        9.5 |   25.0  |   23.7   |   +1.3
       11.0 |   26.5  |   27.5   |   -1.0
       12.5 |   32.5  |   31.4   |   +1.1
       14.0 |   33.5  |   35.2   |   -1.7
       16.0 |   41.0  |   40.4   |   +0.6
  Previsao p/ vento=11 : 27.5 kW pela reta de campo | 27.5 kW pela reta de calibracao
  Leitura              : R^2 = 0.98 indica que 98% da variacao da geracao e explicada pelo vento; inclinacao de campo (2.57) proxima da calibracao (2.50).

============================================================================
  2. TOMADA DE DECISAO AUTOMATICA (REGRAS LOGICAS)
============================================================================
  Entrada              : energia = 40, consumo = 70, previsao eolica = 27.5
  Variaveis Booleanas  : E = 1 (energia < 50) | C = 1 (consumo >= 60) | P = 0 (previsao < 25)
  Saida                : "ALERTA: reduzir consumo"
  Modo Acionado        : MODO ECONOMIA
  Priorizacao          : Manter suporte a vida ligado e desligar sistemas nao essenciais (Laboratorio Cientifico e Mineracao).
  Consumo apos corte   : reduzido de 70.0 kW para 55.0 kW
  Status dos Modulos   :
    - [HAB-01] Suporte a Vida e Habitat     (30.0 kW) -> LIGADO (Prioritario)
    - [MED-01] Suporte Medico               (15.0 kW) -> LIGADO (Prioritario)
    - [COM-01] Comunicacao e Telemetria     (10.0 kW) -> LIGADO (Prioritario)
    - [LAB-01] Laboratorio Cientifico       (10.0 kW) -> DESLIGADO (Economia)
    - [MIN-01] Extracao e Mineracao         ( 5.0 kW) -> DESLIGADO (Economia)

============================================================================
  3. ANALISE DO USO DE ENERGIA (GERACAO VS. CONSUMO)
============================================================================
  [Cenario A - Risco / Deficit Energetico]
  Entrada              : geracao = 40, consumo = 70
  Saida                : "ALERTA: consumo maior que geração"
  Detalhe Operacional  : Deficit de 30.0 kW com reserva baixa (40%): reduzir cargas imediatamente.

  [Cenario B - Eficiencia / Excedente Renovavel]
  Entrada              : geracao = 80, consumo = 30
  Saida                : "SUGESTÃO: armazenar energia excedente"
  Detalhe Operacional  : Excedente de 50.0 kW. Direcionar para recarga do banco de baterias (reserva atual: 85%).

============================================================================
  4. BALANCO INTEGRADO DA COLONIA APOS AUTOMACAO
============================================================================
  Geracao Solar Atual  : 45.0 kW
  Geracao Eolica Prev. : 27.5 kW (para vento = 11 m/s)
  Geracao Total        : 72.5 kW
  Consumo Otimizado    : 55.0 kW
  Saldo                : +17.5 kW
  Diagnostico Final    : "SUGESTÃO: armazenar energia excedente"
  Recomendacao         : Excedente de 17.5 kW. Direcionar para recarga do banco de baterias (reserva atual: 40%).

============================================================================
  5. SIMULACAO MATRICIAL DE CENARIOS (MATRIZ 2D)
============================================================================
  CICLO | VENTO | SOLAR | EOLICA(PREV) | GER.TOTAL | CONSUMO | BAT% | E C P | DECISAO
  ------+-------+-------+--------------+-----------+---------+------+-------+-----------------------------------
    1   |   8.0 |  20.0 |     20.0     |    40.0   |   70.0  |   40 | 1 1 1 | ALERTA: reduzir consumo
        |       |       |              |           |         |      |       | ALERTA: consumo maior que geração
    2   |  11.0 |  45.0 |     27.5     |    72.5   |   55.0  |   45 | 1 0 0 | ALERTA: reduzir consumo
        |       |       |              |           |         |      |       | SUGESTÃO: armazenar energia excedente
    3   |   9.0 |  35.0 |     22.5     |    57.5   |   65.0  |   70 | 0 1 1 | ATENCAO: preparar reserva de energia
        |       |       |              |           |         |      |       | ALERTA: consumo maior que geração
    4   |  12.0 |  50.0 |     30.0     |    80.0   |   30.0  |   85 | 0 0 0 | NORMAL: sistemas estabilizados
        |       |       |              |           |         |      |       | SUGESTÃO: armazenar energia excedente

  [Media por coluna da matriz]
  -> Vento medio ...: 10.00 m/s
  -> Solar medio ...: 37.50 kW
  -> Consumo medio .: 55.00 kW
  -> Bateria media .: 60.00 %

============================================================================
  FIM DA EXECUCAO DO SIGPC - COLONIA AURORA SIGER
============================================================================
```

</details>