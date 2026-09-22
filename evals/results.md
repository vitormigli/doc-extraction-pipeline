# Evaluation Results

| Model | Field accuracy | Valid JSON (1st try) | Valid JSON (final) | Avg cost/doc | Avg latency/doc |
|---|---|---|---|---|---|
| claude-sonnet-5 | 99.5% | 100.0% | 100.0% | $0.0060 | 3.03s |
| claude-haiku-4-5 | 99.0% | 100.0% | 100.0% | $0.0027 | 1.98s |

## Field accuracy by document type

| Model | comprovante_residencia | contracheque | nota_fiscal |
|---|---|---|---|
| claude-sonnet-5 | 98.7% | 100.0% | 100.0% |
| claude-haiku-4-5 | 98.0% | 100.0% | 98.9% |
