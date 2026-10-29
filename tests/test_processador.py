import tempfile
import unittest
from pathlib import Path

from src.processador import calcular_imposto, processar_movimentos


class TestProcessadorMovimentos(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.input_dir = self.base_path / "input"
        self.output_dir = self.base_path / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_calcular_imposto_basico(self):
        self.assertEqual(calcular_imposto(1000.0, 0.05), 50.0)
        self.assertEqual(calcular_imposto(10000.0, 0.0465), 465.0)

    # TODO (Candidato): Implementar testes para:
    # 1. Regras de validação e geração de rejeitados.json sem duplicidade
    # 2. Idempotência: duplicidade exata dentro do mesmo lote e entre lotes
    # 3. Idempotência: rodar processar_movimentos() 2 vezes seguidas produz o mesmo resultado
    # 4. Retificação de valor (atualizado_em mais recente substitui o anterior)
    # 5. Cancelamento de movimento anteriormente ATIVO
    # 6. Evento fora de ordem (atualizado_em mais antigo é ignorado)


if __name__ == '__main__':
    unittest.main()
