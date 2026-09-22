"""Business validation for Brazilian document fields: CPF/CNPJ check digits,
date parsing, and value coherence checks."""

import re
from datetime import date, datetime


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def is_valid_cpf(cpf: str) -> bool:
    d = _digits(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False

    def check_digit(nums: str, weight_start: int) -> int:
        total = sum(
            int(n) * w for n, w in zip(nums, range(weight_start, 1, -1), strict=True)
        )
        r = (total * 10) % 11
        return 0 if r == 10 else r

    d1 = check_digit(d[:9], 10)
    d2 = check_digit(d[:9] + str(d1), 11)
    return d[-2:] == f"{d1}{d2}"


def is_valid_cnpj(cnpj: str) -> bool:
    d = _digits(cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False

    def check_digit(nums: str, weights: list[int]) -> int:
        total = sum(int(n) * w for n, w in zip(nums, weights, strict=True))
        r = total % 11
        return 0 if r < 2 else 11 - r

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = check_digit(d[:12], w1)
    d2 = check_digit(d[:12] + str(d1), w2)
    return d[-2:] == f"{d1}{d2}"


def parse_br_date(value: str) -> date | None:
    """Parse a dd/mm/yyyy date, returning None if invalid."""
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None


def is_coherent_date(value: str, *, min_year: int = 2015, max_year: int = 2030) -> bool:
    parsed = parse_br_date(value)
    if parsed is None:
        return False
    return min_year <= parsed.year <= max_year


def is_coherent_payslip_total(
    salario_bruto: float,
    inss: float,
    irrf: float,
    salario_liquido: float,
    tolerance: float = 0.05,
) -> bool:
    """salario_liquido should equal salario_bruto - inss - irrf within a small
    tolerance (absolute reais), to allow for rounding in synthetic/extracted data."""
    expected = salario_bruto - inss - irrf
    return abs(expected - salario_liquido) <= tolerance
