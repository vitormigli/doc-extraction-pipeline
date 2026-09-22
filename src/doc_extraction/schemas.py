"""Pydantic schemas for the three supported Brazilian document types."""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

from doc_extraction.validators import (
    is_coherent_date,
    is_coherent_payslip_total,
    is_valid_cnpj,
    is_valid_cpf,
)


class DocumentType(StrEnum):
    COMPROVANTE_RESIDENCIA = "comprovante_residencia"
    CONTRACHEQUE = "contracheque"
    NOTA_FISCAL = "nota_fiscal"


class ComprovanteResidencia(BaseModel):
    nome_completo: str
    cpf: str
    endereco: str
    bairro: str
    cidade: str
    estado: str = Field(min_length=2, max_length=2)
    cep: str
    tipo_documento: str
    data_emissao: str
    valor: float | None = None

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        if not is_valid_cpf(v):
            raise ValueError(f"CPF com dígito verificador inválido: {v}")
        return v

    @field_validator("data_emissao")
    @classmethod
    def validate_data(cls, v: str) -> str:
        if not is_coherent_date(v):
            raise ValueError(f"Data de emissão incoerente: {v}")
        return v


class Contracheque(BaseModel):
    nome_funcionario: str
    cpf: str
    empresa: str
    cnpj_empresa: str
    cargo: str
    mes_referencia: str
    salario_bruto: float
    inss: float
    irrf: float
    salario_liquido: float
    data_pagamento: str

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        if not is_valid_cpf(v):
            raise ValueError(f"CPF com dígito verificador inválido: {v}")
        return v

    @field_validator("cnpj_empresa")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        if not is_valid_cnpj(v):
            raise ValueError(f"CNPJ com dígito verificador inválido: {v}")
        return v

    @field_validator("data_pagamento")
    @classmethod
    def validate_data(cls, v: str) -> str:
        if not is_coherent_date(v):
            raise ValueError(f"Data de pagamento incoerente: {v}")
        return v

    @model_validator(mode="after")
    def validate_totais(self) -> "Contracheque":
        if not is_coherent_payslip_total(
            self.salario_bruto, self.inss, self.irrf, self.salario_liquido
        ):
            raise ValueError(
                "Salário líquido não bate com bruto - INSS - IRRF: "
                f"{self.salario_bruto} - {self.inss} - {self.irrf} != {self.salario_liquido}"
            )
        return self


class NotaFiscal(BaseModel):
    numero_nota: str
    cnpj_emitente: str
    razao_social: str
    data_emissao: str
    valor_total: float
    forma_pagamento: str

    @field_validator("cnpj_emitente")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        if not is_valid_cnpj(v):
            raise ValueError(f"CNPJ com dígito verificador inválido: {v}")
        return v

    @field_validator("data_emissao")
    @classmethod
    def validate_data(cls, v: str) -> str:
        if not is_coherent_date(v):
            raise ValueError(f"Data de emissão incoerente: {v}")
        return v

    @field_validator("valor_total")
    @classmethod
    def validate_valor(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"Valor total deve ser positivo: {v}")
        return v


SCHEMA_BY_TYPE: dict[DocumentType, type[BaseModel]] = {
    DocumentType.COMPROVANTE_RESIDENCIA: ComprovanteResidencia,
    DocumentType.CONTRACHEQUE: Contracheque,
    DocumentType.NOTA_FISCAL: NotaFiscal,
}
