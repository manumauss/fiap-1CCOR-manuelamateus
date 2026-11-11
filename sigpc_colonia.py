# -*- coding: utf-8 -*-
# =============================================================================
# SIGPC - Sistema Inteligente de Gestao e Previsao da Colonia
# Missao Aurora Siger (Marte) - Fase 3
# Aluna: Manuela Mateus - RM 576139 | Turma: 1CCOR
# Repositorio: https://github.com/manumauss/fiap-1CCOR-manuelamateus/tree/fase-3
#
# Conceitos utilizados (todos trabalhados nos capitulos da Fase 3):
# - Cap. 2: logica booleana e simplificacao algebrica das regras de decisao;
# - Cap. 3: subalgoritmos (funcoes e procedimentos tipados, parametros default,
#   *args, funcao encadeada e recursividade com condicao de parada);
# - Cap. 4: dicionarios (tabela hash, acesso por chave) e organizacao
#   hierarquica em arvore de subsistemas;
# - Cap. 5: listas (vetores 1D) para series historicas e matriz 2D
#   (lista de listas) para simulacao de cenarios;
# - Cap. 7: regressao linear simples pelo Metodo dos Minimos Quadrados (MMQ);
# - Cap. 8: balanco entre geracao renovavel (solar/eolica), consumo e reserva.
#
# Organizacao do arquivo: 1) DADOS  2) PREVISAO  3) DECISOES  4) ANALISE DE
# ENERGIA  5) EXIBICAO E SIMULACAO  6) PROGRAMA PRINCIPAL.
#
# Execucao: python sigpc_colonia.py   (Python 3, sem bibliotecas externas)
# =============================================================================


# =============================================================================
# 1. ESTRUTURACAO E ORGANIZACAO DOS DADOS DA COLONIA (CAP. 4 E CAP. 5)
# =============================================================================

def inicializar_colonia() -> dict:
    """
    Organiza os dados da colonia em uma arvore de subsistemas (raiz ->
    energetico / ambiental / operacional -> folhas), construida com
    dicionarios aninhados (tabela hash: acesso direto pela chave) e listas
    (vetores 1D) para as series historicas dos sensores.
    """
    colonia = {
        "nome": "Base Aurora Siger - Marte",
        "energetico": {
            "solar": {
                "geracao_atual": 45.0,
                "capacidade_maxima": 100.0,
                "tipo_celula": "Silicio Monocristalino",
                "status": "OPERACIONAL",
            },
            "eolico": {
                "geracao_atual": 25.0,
                "capacidade_maxima": 80.0,
                "tipo_turbina": "Horizontal (HAWT)",
                "cut_in_ms": 3.0,
                "cut_out_ms": 25.0,
                "status": "OPERACIONAL",
            },
            "bateria": {
                "energia_pct": 40.0,
                "capacidade_kwh": 2000.0,
                "modo_sistema": "Off-Grid Autonomo",
            },
        },
        "ambiental": {
            "clima_atual": {
                "vento_ms": 11.0,
                "irradiancia_wm2": 520.0,
                "temp_interna_c": 22.0,
                "temp_externa_c": -55.0,
            },
            # Series historicas em listas (vetores 1D), conforme o enunciado
            # (pontos de calibracao da turbina)
            "historico_vento": [8.0, 10.0, 12.0],
            "historico_energia_eolica": [20.0, 25.0, 30.0],
            # Leituras de campo de 8 sols (anemometro x geracao medida), com a
            # variacao normal dos sensores: servem para validar o modelo
            "leituras_campo": {
                "vento": [5.0, 6.5, 8.0, 9.5, 11.0, 12.5, 14.0, 16.0],
                "energia_eolica": [11.0, 17.5, 19.0, 25.0, 26.5, 32.5, 33.5, 41.0],
            },
        },
        "operacional": {
            "consumo_atual": 70.0,
            "modulos": [
                {"id": "HAB-01", "nome": "Suporte a Vida e Habitat", "consumo": 30.0, "essencial": True, "ativo": True},
                {"id": "MED-01", "nome": "Suporte Medico", "consumo": 15.0, "essencial": True, "ativo": True},
                {"id": "COM-01", "nome": "Comunicacao e Telemetria", "consumo": 10.0, "essencial": True, "ativo": True},
                {"id": "LAB-01", "nome": "Laboratorio Cientifico", "consumo": 10.0, "essencial": False, "ativo": True},
                {"id": "MIN-01", "nome": "Extracao e Mineracao", "consumo": 5.0, "essencial": False, "ativo": True},
            ],
        },
    }
    return colonia


def exibir_hierarquia(no_atual: dict, nivel: int = 0) -> None:
    """
    Procedimento recursivo (Cap. 3) que percorre a arvore de subsistemas e
    exibe cada no com recuo proporcional ao nivel (raiz -> subsistema ->
    componente -> dado). Condicao de parada: o no nao possui filhos (folha).
    """
    recuo = "    " * nivel
    for chave, valor in no_atual.items():
        if isinstance(valor, dict):
            print(f"  {recuo}+-- {chave}")
            exibir_hierarquia(valor, nivel + 1)      # desce um nivel na arvore
        elif isinstance(valor, list):
            print(f"  {recuo}+-- {chave}: lista com {len(valor)} itens")
        else:
            print(f"  {recuo}+-- {chave} = {valor}")


def consultar_subsistema_recursivo(no_atual: dict, chave_alvo: str):
    """
    Funcao recursiva (Cap. 3) que navega na arvore de dicionarios ate
    localizar uma chave. Condicao de parada: a chave esta no nivel atual ou
    nao ha mais subdicionarios a percorrer (retorna None).
    """
    if chave_alvo in no_atual:
        return no_atual[chave_alvo]

    for chave, valor in no_atual.items():
        if isinstance(valor, dict):
            resultado = consultar_subsistema_recursivo(valor, chave_alvo)
            if resultado is not None:
                return resultado
    return None


def somar_cargas(*args: float) -> float:
    """
    Funcao com parametro *args (Cap. 3): soma uma quantidade variavel de
    leituras de geracao ou consumo (ex.: solar + eolica).
    """
    soma = 0.0
    for valor in args:
        soma += valor
    return soma


# =============================================================================
# 2. MODELAGEM E PREVISAO POR REGRESSAO LINEAR SIMPLES (CAP. 7)
# =============================================================================

def ajustar_regressao_linear(x: list, y: list) -> tuple:
    """
    Ajusta a reta y = beta_0 + beta_1 * x pelo Metodo dos Minimos Quadrados
    (MMQ) e calcula o coeficiente de determinacao R^2.
    Retorna a tupla (beta_0, beta_1, r2).
    """
    # Funcao encadeada (Cap. 3): valida tamanho e tipos numericos das series
    def dados_validos(lista_x: list, lista_y: list) -> bool:
        return (
            isinstance(lista_x, list)
            and isinstance(lista_y, list)
            and len(lista_x) == len(lista_y)
            and len(lista_x) >= 2
            and all(
                isinstance(v, (int, float)) and not isinstance(v, bool)
                for v in lista_x + lista_y
            )
        )

    if not dados_validos(x, y):
        return 0.0, 0.0, 0.0

    n = len(x)
    media_x = sum(x) / n
    media_y = sum(y) / n

    # Somatorios dos desvios: Sxy = soma (xi - xm)(yi - ym) ; Sxx = soma (xi - xm)^2
    soma_cov = 0.0
    soma_var_x = 0.0
    for i in range(n):
        desvio_x = x[i] - media_x
        desvio_y = y[i] - media_y
        soma_cov += desvio_x * desvio_y
        soma_var_x += desvio_x ** 2

    beta_1 = soma_cov / soma_var_x if soma_var_x != 0 else 0.0   # inclinacao
    beta_0 = media_y - (beta_1 * media_x)                        # intercepto

    # Coeficiente de determinacao: R^2 = 1 - SQres / SQtot
    sq_residuos = 0.0
    sq_total = 0.0
    for i in range(n):
        y_previsto = beta_0 + (beta_1 * x[i])
        sq_residuos += (y[i] - y_previsto) ** 2
        sq_total += (y[i] - media_y) ** 2

    r2 = 1.0 - (sq_residuos / sq_total) if sq_total != 0 else 1.0
    return beta_0, beta_1, r2


def calcular_residuos(x: list, y: list, beta_0: float, beta_1: float) -> list:
    """
    Calcula o residuo de cada observacao, e_i = y_i - y_prev_i, para a reta
    ajustada. Residuos pequenos e sem padrao indicam que a reta representa
    bem os dados (analise de residuos, Cap. 7).
    Retorna uma lista de listas [x_i, y_i, y_prev_i, e_i].
    """
    tabela = []
    for i in range(len(x)):
        y_previsto = beta_0 + (beta_1 * x[i])
        tabela.append([x[i], y[i], y_previsto, y[i] - y_previsto])
    return tabela


def prever_energia_eolica(vento_entrada: float, beta_0: float, beta_1: float,
                          cut_in: float = 3.0, cut_out: float = 25.0) -> float:
    """
    Aplica a reta ajustada (y_prev = beta_0 + beta_1 * x) para estimar a
    geracao eolica a partir da velocidade do vento.
    Fora da faixa de operacao da turbina (abaixo do cut-in ou acima do
    cut-out, Cap. 8) a turbina nao gera: a previsao e 0 kW. Os limites sao
    parametros default (Cap. 3).
    """
    if vento_entrada < cut_in or vento_entrada > cut_out:
        return 0.0
    previsao = beta_0 + (beta_1 * vento_entrada)
    return previsao if previsao > 0 else 0.0


# =============================================================================
# 3. REGRAS DE DECISAO E LOGICA BOOLEANA (CAP. 2 E CAP. 3)
# =============================================================================

def tomar_decisao_automatica(energia: float, consumo: float,
                             previsao_eolica: float = 25.0,
                             limiar_energia: float = 50.0,
                             limiar_consumo: float = 60.0,
                             limiar_eolica: float = 25.0) -> dict:
    """
    Transforma as leituras em tres variaveis booleanas e aplica as regras
    em ordem de prioridade (if / elif / else):
        E = energia baixa      (energia < 50)
        C = consumo alto       (consumo >= 60)
        P = previsao eolica desfavoravel (previsao < 25 kW)
    A regra "reduzir consumo" vale sempre que E = 1. Pela tabela-verdade,
    X = (E . C') + (E . C) = E . (C' + C) = E . 1 = E  (Cap. 2); por isso o
    alerta aparece nos dois primeiros niveis e so a severidade muda com C.
    Os limiares sao parametros default (Cap. 3).
    """
    energia_baixa = energia < limiar_energia             # E
    consumo_alto = consumo >= limiar_consumo             # C
    previsao_ruim = previsao_eolica < limiar_eolica      # P

    if energia_baixa and consumo_alto:                   # Nivel 1: E . C
        saida_principal = "ALERTA: reduzir consumo"
        modo_operacao = "MODO ECONOMIA"
        acao_priorizacao = (
            "Manter suporte a vida ligado e desligar sistemas nao essenciais "
            "(Laboratorio Cientifico e Mineracao)."
        )
        desligar_nao_essenciais = True
    elif energia_baixa:                                  # Nivel 2: E . C'
        saida_principal = "ALERTA: reduzir consumo"
        modo_operacao = "ALERTA PREVENTIVO"
        acao_priorizacao = (
            "Bateria abaixo de 50% com consumo controlado: manter suporte a "
            "vida prioritario e nao ativar novas cargas."
        )
        desligar_nao_essenciais = False
    elif consumo_alto and previsao_ruim:                 # Nivel 3: E' . C . P
        saida_principal = "ATENCAO: preparar reserva de energia"
        modo_operacao = "RISCO PREDITIVO"
        acao_priorizacao = (
            "Bateria em nivel seguro, porem consumo alto e previsao eolica "
            "baixa: adiar cargas nao essenciais e preservar a reserva."
        )
        desligar_nao_essenciais = False
    else:                                                # Nivel 4
        saida_principal = "NORMAL: sistemas estabilizados"
        modo_operacao = "OPERACAO NOMINAL"
        acao_priorizacao = "Todos os modulos essenciais e cientificos ativos."
        desligar_nao_essenciais = False

    return {
        "saida": saida_principal,
        "modo": modo_operacao,
        "acao": acao_priorizacao,
        "cortar_nao_essenciais": desligar_nao_essenciais,
        "E": int(energia_baixa),
        "C": int(consumo_alto),
        "P": int(previsao_ruim),
    }


def aplicar_priorizacao_modulos(modulos: list, cortar_nao_essenciais: bool) -> float:
    """
    Garante que os modulos essenciais (Suporte a Vida, Medico, Comunicacao)
    permanecam ligados e desliga os nao essenciais quando o modo economia e
    acionado. Retorna o novo consumo total (kW).
    """
    novo_consumo = 0.0
    for mod in modulos:
        if cortar_nao_essenciais and not mod["essencial"]:
            mod["ativo"] = False
        else:
            mod["ativo"] = True

        if mod["ativo"]:
            novo_consumo += mod["consumo"]
    return novo_consumo


# =============================================================================
# 4. ANALISE DO USO DE ENERGIA (CAP. 8)
# =============================================================================

def analisar_uso_energia(geracao: float, consumo: float,
                         reserva_bateria_pct: float = 50.0) -> dict:
    """
    Compara geracao total (solar + eolica), consumo e reserva de bateria.
    consumo > geracao -> risco (deficit) ; geracao > consumo -> excedente
    que pode ser armazenado em vez de desperdicado.
    """
    saldo_kw = geracao - consumo

    if consumo > geracao:
        diagnostico = "ALERTA: consumo maior que geração"
        if reserva_bateria_pct >= 50.0:
            recomendacao = (
                f"Deficit de {abs(saldo_kw):.1f} kW. Reserva de {reserva_bateria_pct:.0f}% "
                f"cobre a diferenca temporariamente; reduzir cargas se persistir."
            )
        else:
            recomendacao = (
                f"Deficit de {abs(saldo_kw):.1f} kW com reserva baixa "
                f"({reserva_bateria_pct:.0f}%): reduzir cargas imediatamente."
            )
    elif geracao > consumo:
        diagnostico = "SUGESTÃO: armazenar energia excedente"
        recomendacao = (
            f"Excedente de {saldo_kw:.1f} kW. Direcionar para recarga do banco de "
            f"baterias (reserva atual: {reserva_bateria_pct:.0f}%)."
        )
    else:
        diagnostico = "EQUILIBRIO: geração igual ao consumo"
        recomendacao = "Balanco energetico nulo. Reserva de bateria mantida."

    return {
        "geracao": geracao,
        "consumo": consumo,
        "saldo": saldo_kw,
        "saida": diagnostico,
        "recomendacao": recomendacao,
    }


# =============================================================================
# 5. PROCEDIMENTOS DE EXIBICAO E SIMULACAO MATRICIAL (CAP. 3 E CAP. 5)
# =============================================================================

def imprimir_cabecalho(titulo: str) -> None:
    """Procedimento (retorno None) para formatar as secoes da saida."""
    print("\n" + "=" * 76)
    print("  " + titulo)
    print("=" * 76)


def simular_matriz_cenarios(beta_0: float, beta_1: float) -> None:
    """
    Usa uma matriz 2D (lista de listas) para simular varios ciclos da
    colonia. Cada linha e um ciclo; as colunas sao:
        [Ciclo, Vento (m/s), Solar (kW), Consumo (kW), Bateria (%)]
    Para cada linha o sistema preve a eolica, decide e analisa o balanco.
    Os quatro cenarios foram escolhidos para acionar cada um dos quatro
    niveis da regra de decisao.
    """
    imprimir_cabecalho("5. SIMULACAO MATRICIAL DE CENARIOS (MATRIZ 2D)")

    matriz_cenarios = [
        # Ciclo, Vento, Solar, Consumo, Bateria
        [1,  8.0, 20.0, 70.0, 40.0],   # bateria baixa + consumo alto      -> Nivel 1
        [2, 11.0, 45.0, 55.0, 45.0],   # bateria baixa + consumo controlado -> Nivel 2
        [3,  9.0, 35.0, 65.0, 70.0],   # bateria ok + consumo alto + vento fraco -> Nivel 3
        [4, 12.0, 50.0, 30.0, 85.0],   # tudo favoravel                     -> Nivel 4
    ]

    print("  CICLO | VENTO | SOLAR | EOLICA(PREV) | GER.TOTAL | CONSUMO | BAT% | E C P | DECISAO")
    print("  ------+-------+-------+--------------+-----------+---------+------+-------+-----------------------------------")

    soma_colunas = [0.0, 0.0, 0.0, 0.0]      # vento, solar, consumo, bateria

    for linha in matriz_cenarios:
        ciclo = int(linha[0])
        vento = linha[1]
        solar = linha[2]
        consumo = linha[3]
        bateria = linha[4]

        eolica_prev = prever_energia_eolica(vento, beta_0, beta_1)
        geracao_total = somar_cargas(solar, eolica_prev)
        decisao = tomar_decisao_automatica(bateria, consumo, eolica_prev)
        analise = analisar_uso_energia(geracao_total, consumo, bateria)

        print(f"    {ciclo}   | {vento:5.1f} | {solar:5.1f} |    {eolica_prev:5.1f}     |"
              f"   {geracao_total:5.1f}   |  {consumo:5.1f}  | {bateria:4.0f} |"
              f" {decisao['E']} {decisao['C']} {decisao['P']} | {decisao['saida']}")
        print(f"        |       |       |              |           |         |      |       | "
              f"{analise['saida']}")

        # Agregacao por coluna da matriz (percorrendo as colunas 1 a 4)
        for j in range(1, 5):
            soma_colunas[j - 1] += linha[j]

    n_linhas = len(matriz_cenarios)
    print("\n  [Media por coluna da matriz]")
    print(f"  -> Vento medio ...: {soma_colunas[0] / n_linhas:.2f} m/s")
    print(f"  -> Solar medio ...: {soma_colunas[1] / n_linhas:.2f} kW")
    print(f"  -> Consumo medio .: {soma_colunas[2] / n_linhas:.2f} kW")
    print(f"  -> Bateria media .: {soma_colunas[3] / n_linhas:.2f} %")


# =============================================================================
# 6. PROGRAMA PRINCIPAL (EXECUCAO INTEGRADA DOS CASOS DO ENUNCIADO)
# =============================================================================

def executar_sigpc() -> None:
    """Procedimento principal: orquestra dados -> previsao -> decisao -> analise."""
    imprimir_cabecalho("SIGPC - SISTEMA INTELIGENTE DA COLONIA AURORA SIGER (FASE 3)")

    # 1. Dados: arvore de subsistemas + tabela hash + listas
    colonia = inicializar_colonia()
    print(f"  Colonia Inicializada : {colonia['nome']}")
    print(f"  Modo de Operacao     : {colonia['energetico']['bateria']['modo_sistema']}")
    print("  Arvore de subsistemas (raiz -> subsistema -> componente -> dado):")
    exibir_hierarquia(colonia)

    # Navegacao recursiva ate uma chave da arvore
    clima = consultar_subsistema_recursivo(colonia, "clima_atual")
    print(f"\n  Busca recursiva 'clima_atual' -> Vento = {clima['vento_ms']} m/s | "
          f"Irradiancia = {clima['irradiancia_wm2']} W/m2 | "
          f"Temp. Externa = {clima['temp_externa_c']} C")

    # 2. Previsao com regressao linear simples
    imprimir_cabecalho("1. PREVISAO DE GERACAO EOLICA (REGRESSAO LINEAR SIMPLES)")
    vento_hist = colonia["ambiental"]["historico_vento"]
    energia_hist = colonia["ambiental"]["historico_energia_eolica"]

    beta_0, beta_1, r2 = ajustar_regressao_linear(vento_hist, energia_hist)
    vento_teste = clima["vento_ms"]                       # 11 m/s
    previsao = prever_energia_eolica(vento_teste, beta_0, beta_1)

    print(f"  Dados Historicos     : vento = {vento_hist} m/s | energia = {energia_hist} kW")
    print(f"  Reta Ajustada (MMQ)  : Energia = {beta_0:.2f} + {beta_1:.2f} * Vento  (R^2 = {r2:.2f})")
    print(f"  Entrada              : vento = {vento_teste:.0f}")
    print(f"  Saida                : previsao de energia = {previsao:.1f} kW")

    # A previsao atualiza a geracao eolica na arvore da colonia
    colonia["energetico"]["eolico"]["geracao_atual"] = previsao

    # Validacao do modelo com leituras de campo: aqui os pontos nao estao
    # alinhados, entao o R^2 e os residuos mostram a qualidade real do ajuste
    campo = consultar_subsistema_recursivo(colonia, "leituras_campo")
    b0_campo, b1_campo, r2_campo = ajustar_regressao_linear(campo["vento"], campo["energia_eolica"])
    previsao_campo = prever_energia_eolica(vento_teste, b0_campo, b1_campo)

    print("\n  [Validacao do modelo com 8 leituras de campo]")
    print(f"  Vento medido (m/s)   : {campo['vento']}")
    print(f"  Eolica medida (kW)   : {campo['energia_eolica']}")
    print(f"  Reta Ajustada (MMQ)  : Energia = {b0_campo:.2f} + {b1_campo:.2f} * Vento  (R^2 = {r2_campo:.2f})")
    print("  Residuos (e = y - y_prev):")
    print("      vento |  medido | previsto | residuo")
    for x_i, y_i, y_prev, e_i in calcular_residuos(campo["vento"], campo["energia_eolica"], b0_campo, b1_campo):
        print(f"      {x_i:5.1f} |  {y_i:5.1f}  |  {y_prev:5.1f}   |  {e_i:+5.1f}")
    print(f"  Previsao p/ vento=11 : {previsao_campo:.1f} kW pela reta de campo | "
          f"{previsao:.1f} kW pela reta de calibracao")
    print(f"  Leitura              : R^2 = {r2_campo:.2f} indica que {r2_campo * 100:.0f}% da variacao da geracao e "
          f"explicada pelo vento; inclinacao de campo ({b1_campo:.2f}) proxima da calibracao ({beta_1:.2f}).")

    # 3. Tomada de decisao automatica (logica booleana)
    imprimir_cabecalho("2. TOMADA DE DECISAO AUTOMATICA (REGRAS LOGICAS)")
    energia_in = colonia["energetico"]["bateria"]["energia_pct"]   # 40 %
    consumo_in = colonia["operacional"]["consumo_atual"]           # 70 kW

    decisao = tomar_decisao_automatica(energia_in, consumo_in, previsao)
    print(f"  Entrada              : energia = {energia_in:.0f}, consumo = {consumo_in:.0f}, "
          f"previsao eolica = {previsao:.1f}")
    print(f"  Variaveis Booleanas  : E = {decisao['E']} (energia < 50) | "
          f"C = {decisao['C']} (consumo >= 60) | P = {decisao['P']} (previsao < 25)")
    print(f"  Saida                : \"{decisao['saida']}\"")
    print(f"  Modo Acionado        : {decisao['modo']}")
    print(f"  Priorizacao          : {decisao['acao']}")

    novo_consumo = aplicar_priorizacao_modulos(
        colonia["operacional"]["modulos"],
        decisao["cortar_nao_essenciais"]
    )
    if decisao["cortar_nao_essenciais"]:
        print(f"  Consumo apos corte   : reduzido de {consumo_in:.1f} kW para {novo_consumo:.1f} kW")
    else:
        print(f"  Consumo              : mantido em {novo_consumo:.1f} kW (sem corte de cargas)")
    print("  Status dos Modulos   :")
    for mod in colonia["operacional"]["modulos"]:
        estado = "LIGADO (Prioritario)" if mod["ativo"] else "DESLIGADO (Economia)"
        print(f"    - [{mod['id']}] {mod['nome'].ljust(28)} ({mod['consumo']:4.1f} kW) -> {estado}")

    # 4. Analise do uso de energia (casos exatos do enunciado)
    imprimir_cabecalho("3. ANALISE DO USO DE ENERGIA (GERACAO VS. CONSUMO)")

    # Caso A do enunciado: geracao = 40, consumo = 70
    caso_deficit = analisar_uso_energia(geracao=40.0, consumo=70.0, reserva_bateria_pct=energia_in)
    print("  [Cenario A - Risco / Deficit Energetico]")
    print(f"  Entrada              : geracao = {caso_deficit['geracao']:.0f}, consumo = {caso_deficit['consumo']:.0f}")
    print(f"  Saida                : \"{caso_deficit['saida']}\"")
    print(f"  Detalhe Operacional  : {caso_deficit['recomendacao']}\n")

    # Caso B do enunciado: geracao = 80, consumo = 30
    caso_superavit = analisar_uso_energia(geracao=80.0, consumo=30.0, reserva_bateria_pct=85.0)
    print("  [Cenario B - Eficiencia / Excedente Renovavel]")
    print(f"  Entrada              : geracao = {caso_superavit['geracao']:.0f}, consumo = {caso_superavit['consumo']:.0f}")
    print(f"  Saida                : \"{caso_superavit['saida']}\"")
    print(f"  Detalhe Operacional  : {caso_superavit['recomendacao']}")

    # 5. Balanco integrado: previsao eolica + corte de carga
    imprimir_cabecalho("4. BALANCO INTEGRADO DA COLONIA APOS AUTOMACAO")
    ger_solar = colonia["energetico"]["solar"]["geracao_atual"]
    ger_eolica = colonia["energetico"]["eolico"]["geracao_atual"]
    ger_total_colonia = somar_cargas(ger_solar, ger_eolica)
    analise_pos = analisar_uso_energia(ger_total_colonia, novo_consumo, energia_in)

    print(f"  Geracao Solar Atual  : {ger_solar:.1f} kW")
    print(f"  Geracao Eolica Prev. : {ger_eolica:.1f} kW (para vento = {vento_teste:.0f} m/s)")
    print(f"  Geracao Total        : {ger_total_colonia:.1f} kW")
    print(f"  Consumo Otimizado    : {novo_consumo:.1f} kW")
    print(f"  Saldo                : {analise_pos['saldo']:+.1f} kW")
    print(f"  Diagnostico Final    : \"{analise_pos['saida']}\"")
    print(f"  Recomendacao         : {analise_pos['recomendacao']}")

    # 6. Simulacao matricial de varios ciclos (aciona os 4 niveis de decisao)
    simular_matriz_cenarios(beta_0, beta_1)

    imprimir_cabecalho("FIM DA EXECUCAO DO SIGPC - COLONIA AURORA SIGER")


if __name__ == "__main__":
    executar_sigpc()