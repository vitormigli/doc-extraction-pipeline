"""Synthetic data + document image generation for the three supported document types."""

import random

from faker import Faker
from PIL.Image import Image

from doc_extraction.generator.render import degrade, render_document
from doc_extraction.schemas import DocumentType

fake = Faker("pt_BR")

TIPOS_COMPROVANTE = ["Conta de Água", "Conta de Luz", "Conta de Telefone", "Conta de Internet"]
CARGOS = [
    "Analista de Sistemas",
    "Assistente Administrativo",
    "Técnico em Automação",
    "Engenheiro de Software",
    "Analista Financeiro",
    "Coordenador de Operações",
]
FORMAS_PAGAMENTO = ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Pix", "Boleto"]


def _brl(value: float) -> str:
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def generate_comprovante_residencia(seed: int) -> tuple[dict, Image]:
    fake.seed_instance(seed)
    rng = random.Random(seed)

    nome = fake.name()
    cpf = fake.cpf()
    endereco = fake.street_address()
    bairro = fake.bairro()
    cidade = fake.city()
    estado = fake.estado_sigla()
    cep_digits = "".join(c for c in fake.postcode() if c.isdigit())
    cep = f"{cep_digits[:5]}-{cep_digits[5:]}"
    tipo = rng.choice(TIPOS_COMPROVANTE)
    data_emissao = fake.date_between(start_date="-1y", end_date="today").strftime("%d/%m/%Y")
    valor = round(rng.uniform(40, 450), 2)

    data = {
        "nome_completo": nome,
        "cpf": cpf,
        "endereco": endereco,
        "bairro": bairro,
        "cidade": cidade,
        "estado": estado,
        "cep": cep,
        "tipo_documento": tipo,
        "data_emissao": data_emissao,
        "valor": valor,
    }

    lines = [
        f"Titular: {nome}",
        f"CPF: {cpf}",
        f"Endereço: {endereco}",
        f"Bairro: {bairro}",
        f"Cidade/UF: {cidade}/{estado}",
        f"CEP: {cep}",
        f"Data de emissão: {data_emissao}",
        f"Valor: {_brl(valor)}",
    ]
    img = render_document(tipo, lines)
    return data, img


def generate_contracheque(seed: int) -> tuple[dict, Image]:
    fake.seed_instance(seed)
    rng = random.Random(seed)

    nome = fake.name()
    cpf = fake.cpf()
    empresa = fake.company()
    cnpj = fake.cnpj()
    cargo = rng.choice(CARGOS)
    mes_ref = fake.date_between(start_date="-1y", end_date="today").strftime("%m/%Y")
    salario_bruto = round(rng.uniform(2200, 12000), 2)
    inss = round(salario_bruto * rng.uniform(0.08, 0.11), 2)
    irrf = round(salario_bruto * rng.uniform(0.0, 0.15), 2)
    salario_liquido = round(salario_bruto - inss - irrf, 2)
    data_pagamento = fake.date_between(start_date="-1y", end_date="today").strftime("%d/%m/%Y")

    data = {
        "nome_funcionario": nome,
        "cpf": cpf,
        "empresa": empresa,
        "cnpj_empresa": cnpj,
        "cargo": cargo,
        "mes_referencia": mes_ref,
        "salario_bruto": salario_bruto,
        "inss": inss,
        "irrf": irrf,
        "salario_liquido": salario_liquido,
        "data_pagamento": data_pagamento,
    }

    lines = [
        f"Funcionário: {nome}",
        f"CPF: {cpf}",
        f"Empresa: {empresa}",
        f"CNPJ: {cnpj}",
        f"Cargo: {cargo}",
        f"Mês de referência: {mes_ref}",
        f"Salário bruto: {_brl(salario_bruto)}",
        f"INSS: {_brl(inss)}",
        f"IRRF: {_brl(irrf)}",
        f"Salário líquido: {_brl(salario_liquido)}",
        f"Data de pagamento: {data_pagamento}",
    ]
    img = render_document("Contracheque", lines)
    return data, img


def generate_nota_fiscal(seed: int) -> tuple[dict, Image]:
    fake.seed_instance(seed)
    rng = random.Random(seed)

    numero_nota = str(rng.randint(100000, 999999))
    cnpj = fake.cnpj()
    razao_social = fake.company()
    data_emissao = fake.date_between(start_date="-1y", end_date="today").strftime("%d/%m/%Y")
    valor_total = round(rng.uniform(15, 3500), 2)
    forma_pagamento = rng.choice(FORMAS_PAGAMENTO)

    data = {
        "numero_nota": numero_nota,
        "cnpj_emitente": cnpj,
        "razao_social": razao_social,
        "data_emissao": data_emissao,
        "valor_total": valor_total,
        "forma_pagamento": forma_pagamento,
    }

    lines = [
        f"Nota Fiscal nº {numero_nota}",
        f"Emitente: {razao_social}",
        f"CNPJ: {cnpj}",
        f"Data de emissão: {data_emissao}",
        f"Valor total: {_brl(valor_total)}",
        f"Forma de pagamento: {forma_pagamento}",
    ]
    img = render_document("Nota Fiscal Simplificada", lines)
    return data, img


GENERATOR_BY_TYPE = {
    DocumentType.COMPROVANTE_RESIDENCIA: generate_comprovante_residencia,
    DocumentType.CONTRACHEQUE: generate_contracheque,
    DocumentType.NOTA_FISCAL: generate_nota_fiscal,
}


def generate_document(doc_type: DocumentType, seed: int, *, degrade_image: bool = True):
    data, img = GENERATOR_BY_TYPE[doc_type](seed)
    if degrade_image:
        img = degrade(img, seed=seed)
    return data, img
