import pytest
from pydantic import ValidationError

from doc_extraction.schemas import Contracheque, NotaFiscal


def test_contracheque_rejects_invalid_cpf():
    with pytest.raises(ValidationError):
        Contracheque(
            nome_funcionario="Sophia Cavalcanti",
            cpf="934.786.521-00",
            empresa="Caldeira",
            cnpj_empresa="17.493.806/0001-61",
            cargo="Analista Financeiro",
            mes_referencia="05/2026",
            salario_bruto=7177.15,
            inss=695.81,
            irrf=989.12,
            salario_liquido=5492.22,
            data_pagamento="23/09/2025",
        )


def test_contracheque_rejects_incoherent_total():
    with pytest.raises(ValidationError):
        Contracheque(
            nome_funcionario="Sophia Cavalcanti",
            cpf="934.786.521-46",
            empresa="Caldeira",
            cnpj_empresa="17.493.806/0001-61",
            cargo="Analista Financeiro",
            mes_referencia="05/2026",
            salario_bruto=7177.15,
            inss=695.81,
            irrf=989.12,
            salario_liquido=1000.00,
            data_pagamento="23/09/2025",
        )


def test_contracheque_accepts_valid_data():
    slip = Contracheque(
        nome_funcionario="Sophia Cavalcanti",
        cpf="934.786.521-46",
        empresa="Caldeira",
        cnpj_empresa="17.493.806/0001-61",
        cargo="Analista Financeiro",
        mes_referencia="05/2026",
        salario_bruto=7177.15,
        inss=695.81,
        irrf=989.12,
        salario_liquido=5492.22,
        data_pagamento="23/09/2025",
    )
    assert slip.salario_liquido == 5492.22


def test_nota_fiscal_rejects_negative_value():
    with pytest.raises(ValidationError):
        NotaFiscal(
            numero_nota="123456",
            cnpj_emitente="17.493.806/0001-61",
            razao_social="Caldeira",
            data_emissao="23/09/2025",
            valor_total=-10.0,
            forma_pagamento="Pix",
        )
