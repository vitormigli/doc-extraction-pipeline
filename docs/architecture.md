# Architecture

```mermaid
flowchart TD
    A[Document image] --> B[Claude vision + tool_use]
    B --> C{Pydantic validation}
    C -- valid --> D[Structured JSON]
    C -- invalid --> E[Retry: validation error fed back to model]
    E --> B
    C -- invalid after retry --> F[422 error with raw output]
    D --> G[Business rules: CPF/CNPJ digit check, date/value coherence]
```

The extraction schema is generated from the same Pydantic model used for validation
(`model_json_schema()`), so the tool definition sent to Claude and the validator that
checks its output can never drift apart.
