import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "output"


def carregar_lotes(input_dir: Path = INPUT_DIR) -> List[Dict[str, Any]]:
    """Lê todos os arquivos lote_*.json do diretório de entrada."""
    registros: List[Dict[str, Any]] = []
    for arquivo in sorted(input_dir.glob("lote_*.json")):
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
            registros.extend(dados)
    return registros


def validar_movimento(movimento: Dict[str, Any]) -> bool:
    """
    Valida se o movimento fiscal pode ser processado.
    FIXME: Atualmente valida apenas valor_base > 0.
    Faltam as demais regras de negócio e o retorno do motivo de rejeição.
    """
    if movimento.get("valor_base", 0) <= 0:
        return False

    return True


def calcular_imposto(valor_base: float | int, aliquota: float | int) -> float | int:
    """Calcula o imposto retido arredondado em 2 casas decimais."""
    return round(valor_base * aliquota, 2)


def processar_movimentos(
    input_dir: Path = INPUT_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> List[Dict[str, Any]]:
    """
    Processa os lotes de entrada e gera o arquivo consolidado.
    ATENÇÃO: Este código legado NÃO é idempotente e possui bugs conhecidos!
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    arquivo_consolidado = output_dir / "consolidado.json"

    # Carrega consolidado existente (se houver) para acumular
    grupos: Dict[tuple, Dict[str, Any]] = {}
    if arquivo_consolidado.exists():
        with open(arquivo_consolidado, "r", encoding="utf-8") as f:
            existentes = json.load(f)
            for item in existentes:
                chave = (item["competencia"], item["cnpj"], item["tipo_imposto"])
                grupos[chave] = item

    movimentos = carregar_lotes(input_dir)
    lidos = 0
    processados = 0
    rejeitados = 0

    for mov in movimentos:
        lidos += 1
        if not validar_movimento(mov):
            rejeitados += 1
            continue

        if mov.get("status") != "ATIVO":
            continue

        chave = (mov["competencia"], mov["cnpj"], mov["tipo_imposto"])
        imposto = calcular_imposto(mov["valor_base"], mov["aliquota"])

        if chave not in grupos:
            grupos[chave] = {
                "competencia": mov["competencia"],
                "cnpj": mov["cnpj"],
                "tipo_imposto": mov["tipo_imposto"],
                "quantidade_movimentos_ativos": 0,
                "valor_base_total": 0.0,
                "valor_imposto_total": 0.0,
            }

        grupos[chave]["quantidade_movimentos_ativos"] += 1
        grupos[chave]["valor_base_total"] = round(
            grupos[chave]["valor_base_total"] + mov["valor_base"], 2
        )
        grupos[chave]["valor_imposto_total"] = round(
            grupos[chave]["valor_imposto_total"] + imposto, 2
        )
        processados += 1

    resultado = sorted(
        grupos.values(),
        key=lambda x: (x["competencia"], x["cnpj"], x["tipo_imposto"]),
    )

    with open(arquivo_consolidado, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(
        f"[RESUMO] Lidos: {lidos} | Processados: {processados} | Rejeitados: {rejeitados}"
    )
    return resultado


if __name__ == "__main__":
    processar_movimentos()
