"""Structured extraction from a document image using Claude's vision + tool use,
validated against the Pydantic schema for the given document type, with one retry
on validation failure (the validation error is fed back to the model)."""

import base64
import time
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic
from pydantic import BaseModel, ValidationError

from doc_extraction.schemas import SCHEMA_BY_TYPE, DocumentType

DEFAULT_MODEL = "claude-sonnet-5"
MAX_RETRIES = 1

_PROMPTS = {
    DocumentType.COMPROVANTE_RESIDENCIA: (
        "Extract the fields from this Brazilian proof-of-residence document "
        "(comprovante de residência) as JSON matching this schema: nome_completo, cpf "
        "(format xxx.xxx.xxx-xx), endereco, bairro, cidade, estado (2-letter UF), cep, "
        "tipo_documento, data_emissao (dd/mm/yyyy), valor (number or null)."
    ),
    DocumentType.CONTRACHEQUE: (
        "Extract the fields from this Brazilian payslip (contracheque) as JSON matching "
        "this schema: nome_funcionario, cpf (xxx.xxx.xxx-xx), empresa, cnpj_empresa "
        "(xx.xxx.xxx/xxxx-xx), cargo, mes_referencia (mm/yyyy), salario_bruto (number), "
        "inss (number), irrf (number), salario_liquido (number), data_pagamento (dd/mm/yyyy)."
    ),
    DocumentType.NOTA_FISCAL: (
        "Extract the fields from this simplified Brazilian invoice (nota fiscal) as JSON "
        "matching this schema: numero_nota, cnpj_emitente (xx.xxx.xxx/xxxx-xx), "
        "razao_social, data_emissao (dd/mm/yyyy), valor_total (number), forma_pagamento."
    ),
}

_TOOL_NAME = "submit_extraction"


def _schema_tool(document_type: DocumentType) -> dict:
    schema_model: type[BaseModel] = SCHEMA_BY_TYPE[document_type]
    json_schema = schema_model.model_json_schema()
    json_schema.pop("title", None)
    return {
        "name": _TOOL_NAME,
        "description": "Submit the extracted, structured document fields.",
        "input_schema": json_schema,
    }


@dataclass
class ExtractionResult:
    document_type: DocumentType
    raw_output: dict | None
    validated: BaseModel | None
    valid_on_first_try: bool
    attempts: int
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    error: str | None = None
    model: str = DEFAULT_MODEL
    strategy: str = "tool_use"


def _image_block(image_path: Path) -> dict:
    data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": data},
    }


def extract_document(
    image_path: Path,
    document_type: DocumentType,
    *,
    client: Anthropic | None = None,
    model: str = DEFAULT_MODEL,
    max_retries: int = MAX_RETRIES,
) -> ExtractionResult:
    client = client or Anthropic()
    tool = _schema_tool(document_type)
    prompt = _PROMPTS[document_type]

    messages: list[dict] = [
        {
            "role": "user",
            "content": [
                _image_block(image_path),
                {"type": "text", "text": prompt},
            ],
        }
    ]

    start = time.monotonic()
    total_input_tokens = 0
    total_output_tokens = 0
    last_raw: dict | None = None
    last_error: str | None = None

    for attempt in range(max_retries + 1):
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=[tool],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=messages,
        )
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_use is None:
            last_error = "Model did not return a tool_use block"
            break

        last_raw = tool_use.input
        schema_model = SCHEMA_BY_TYPE[document_type]
        try:
            validated = schema_model(**last_raw)
            latency = time.monotonic() - start
            return ExtractionResult(
                document_type=document_type,
                raw_output=last_raw,
                validated=validated,
                valid_on_first_try=(attempt == 0),
                attempts=attempt + 1,
                latency_seconds=latency,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                model=model,
            )
        except ValidationError as e:
            last_error = str(e)
            if attempt < max_retries:
                messages.append({"role": "assistant", "content": response.content})
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": (
                                    "Validation failed, please correct and resubmit: "
                                    f"{last_error}"
                                ),
                                "is_error": True,
                            }
                        ],
                    }
                )

    latency = time.monotonic() - start
    return ExtractionResult(
        document_type=document_type,
        raw_output=last_raw,
        validated=None,
        valid_on_first_try=False,
        attempts=max_retries + 1,
        latency_seconds=latency,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        error=last_error,
        model=model,
    )
