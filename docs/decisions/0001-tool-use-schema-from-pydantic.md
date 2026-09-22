# 1. Generate the Claude tool schema from the Pydantic model

## Status

Accepted

## Context

We need Claude to return structured output for each document type, and we need to
validate that output against business rules (CPF/CNPJ check digits, coherent dates and
totals). Maintaining two separate schema definitions — one for the Claude tool
definition and one for validation — risks them drifting apart.

## Decision

Define each document type once as a Pydantic model, then derive the Claude tool's
`input_schema` from it via `model_json_schema()`. Force tool use
(`tool_choice: {"type": "tool", ...}`) so Claude always returns the tool call rather
than free text.

## Consequences

- One source of truth per document type.
- Business rules (CPF/CNPJ, coherence) run as Pydantic validators, so they apply
  identically whether the input came from the model or from a test.
- If a field needs a custom validator, it must be expressed as something
  `model_json_schema()` can represent, or added as a `model_validator` that runs after
  the JSON-schema-level shape check.
