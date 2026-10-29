# Case Técnico — Consolidador Idempotente de Movimentos Fiscais

## 1. Contexto

Nossa área possui um script local (`src/processador.py`) responsável por ler lotes de movimentos fiscais (retenção de impostos sobre notas de serviço) na pasta `data/input/` e gerar o relatório consolidado do mês em `data/output/consolidado.json`.

Recentemente, identificamos problemas graves na rotina atual:

1. **Falta de idempotência na reexecução:** Se o script for executado duas vezes seguidas, ou se um arquivo for reprocessado, os valores consolidados dobram.
2. **Duplicidade dentro dos lotes:** O sistema emissor às vezes envia o mesmo `id_movimento` repetido dentro do mesmo arquivo ou em arquivos diferentes.
3. **Atualizações e cancelamentos ignorados:** Um movimento já enviado pode sofrer retificação (novo valor) ou cancelamento em um lote posterior, mas o código atual apenas soma tudo cegamente.
4. **Validações incompletas:** Registros com dados inválidos estão entrando na conta ou causando distorções sem gerar a trilha de auditoria em `data/output/rejeitados.json`.

---

## 2. Seu Desafio

Você deve evoluir e refatorar o código existente (`src/processador.py` — podendo criar novos módulos se desejar) para torná-lo **idempotente, resiliente e testado**.

> **Regra de ouro da idempotência:**
>
> 1. Processar todos os lotes juntos 1 vez, 2 vezes ou 10 vezes seguidas deve produzir exatamente o mesmo resultado final nos arquivos de saída.
> 2. Processar os lotes de forma incremental (ex.: rodar o processador hoje apenas com `lote_01.json`, e depois rodar apenas com `lote_02.json` e `lote_03.json` apontando para o mesmo `output_dir`) também deve produzir exatamente o mesmo resultado final.

> **Sobre o uso de IA (Copilot, ChatGPT, Claude, etc.):** O uso de ferramentas de IA é permitido, assim como no nosso dia a dia. Porém, na etapa de apresentação você será avaliado pelo domínio total sobre o código entregue, pelas decisões de design, pela revisão crítica do que a IA gerou e por uma pequena evolução ao vivo no seu código durante a banca.

---

## 3. Formato dos Dados de Entrada (`data/input/lote_*.json`)

Cada arquivo contém uma lista de objetos JSON com os campos:

```json
{
  "id_movimento": "MOV-001",
  "cnpj": "11111111000111",
  "competencia": "2026-04",
  "tipo_imposto": "ISS",
  "valor_base": 1000.00,
  "aliquota": 0.05,
  "status": "ATIVO",
  "atualizado_em": "2026-04-10T10:00:00"
}
```

---

## 4. Regras de Negócio Obrigatórias

### 4.1. Validação (Críticas de Entrada)

Um registro é considerado **inválido (rejeitado)** se violar qualquer uma das regras abaixo:

- `id_movimento` ausente ou vazio;
- `cnpj` não conter exatamente 14 dígitos numéricos (`0-9`);
- `competencia` não estar no formato `YYYY-MM` com mês entre `01` e `12`;
- `tipo_imposto` não ser um dos valores permitidos: `"ISS"`, `"IRRF"` ou `"PIS_COFINS"`;
- `valor_base` ser menor ou igual a `0`;
- `aliquota` ser menor ou igual a `0` ou maior que `1.0`;
- `status` não ser `"ATIVO"` nem `"CANCELADO"`;
- `atualizado_em` ausente ou em formato ISO-8601 inválido.

**Comportamento para inválidos:**

- Não devem entrar no cálculo do consolidado nem alterar o estado de um movimento válido anterior.
- Devem ser registrados em `data/output/rejeitados.json` contendo o registro original e o campo `"motivo_rejeicao"`.
- Atenção à idempotência também nos rejeitados: rodar o script várias vezes não pode duplicar o mesmo registro idêntico dentro de `rejeitados.json`.

### 4.2. Idempotência, Retificação e Cancelamento

Para todos os registros válidos, a chave de negócio do movimento é o `id_movimento`:

1. **Duplicidade exata (`atualizado_em` igual):** Se um `id_movimento` já conhecido aparecer novamente com o mesmo timestamp `atualizado_em` (no mesmo arquivo, em outro arquivo ou numa reexecução do script), ele deve ser ignorado (contabilizado apenas uma única vez).
2. **Retificação ou Cancelamento (`atualizado_em` mais recente):** Se o mesmo `id_movimento` chegar com um `atualizado_em` maior (mais recente) que o já registrado:
   - O estado novo substitui o estado anterior daquele movimento.
   - Se o novo `status` for `"ATIVO"`, o consolidado passa a considerar o novo `valor_base` e a nova `aliquota`.
   - Se o novo `status` for `"CANCELADO"`, o movimento deixa de compor a soma e a contagem de ativos do consolidado.
3. **Evento atrasado / fora de ordem (`atualizado_em` mais antigo):** Se chegar um evento para um `id_movimento` com `atualizado_em` menor (mais antigo) do que a versão já conhecida daquele movimento, ele deve ser ignorado.

### 4.3. Cálculo do Imposto e Consolidação

- Para cada movimento válido cujo estado final (mais recente) seja `status == "ATIVO"`:
  - `valor_imposto = round(valor_base * aliquota, 2)`
- O arquivo `data/output/consolidado.json` deve agrupar os movimentos ativos por `(competencia, cnpj, tipo_imposto)` (ordenado por esses 3 campos) no formato:

```json
[
  {
    "competencia": "2026-04",
    "cnpj": "11111111000111",
    "tipo_imposto": "ISS",
    "quantidade_movimentos_ativos": 2,
    "valor_base_total": 3000.0,
    "valor_imposto_total": 150.0
  }
]
```

*(Se um grupo ficar com `0` movimentos ativos após um cancelamento, ele não deve aparecer no `consolidado.json` ou deve ser omitido).*

---

## 5. Como Executar o Projeto Atual

Não é necessário instalar bibliotecas externas (apenas Python 3.9+ padrão; `pytest` é opcional).

Para rodar o processador atual:

```bash
python -m src.processador
```

Para rodar os testes unitários:

```bash
python -m unittest discover -s tests -v
```

---

## 6. Entregáveis Esperados

1. Código refatorado garantindo todas as regras de validação e idempotência (mesmo quando executado múltiplas vezes seguidas).
2. Testes automatizados em `tests/test_processador.py` cobrindo validação, duplicidade, retificação, cancelamento, eventos fora de ordem e reexecução idempotente.
3. Respostas no final deste README (seção 7 abaixo) explicando brevemente sua solução.

---

## 7. Documentação da Solução (Preencher pelo Candidato)

### 7.1. Quais eram os problemas do código original?

*(Descreva aqui o que você encontrou)*

### 7.2. Como você garantiu a idempotência (tanto na reexecução total quanto na chegada incremental de lotes)?

*(Explique sua estratégia de armazenamento de estado / deduplicação)*

### 7.3. Uso de IA no Desenvolvimento

*(Seja transparente — isso conta pontos a favor da sua maturidade técnica)*

- Como você utilizou IA para apoiar na resolução?
- O que a IA sugeriu/gerou inicialmente que estava incorreto, incompleto ou não atendia algum caso de borda dos lotes, e como você identificou e corrigiu?
