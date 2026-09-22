from doc_extraction.validators import (
    is_coherent_date,
    is_coherent_payslip_total,
    is_valid_cnpj,
    is_valid_cpf,
)


def test_valid_cpf():
    assert is_valid_cpf("862.357.940-29")


def test_invalid_cpf_wrong_digit():
    assert not is_valid_cpf("862.357.940-00")


def test_invalid_cpf_all_same_digit():
    assert not is_valid_cpf("111.111.111-11")


def test_valid_cnpj():
    assert is_valid_cnpj("17.493.806/0001-61")


def test_invalid_cnpj_wrong_digit():
    assert not is_valid_cnpj("17.493.806/0001-00")


def test_coherent_date():
    assert is_coherent_date("25/04/2026")


def test_incoherent_date_bad_format():
    assert not is_coherent_date("2026-04-25")


def test_incoherent_date_out_of_range():
    assert not is_coherent_date("25/04/1990")


def test_coherent_payslip_total():
    assert is_coherent_payslip_total(7177.15, 695.81, 989.12, 5492.22)


def test_incoherent_payslip_total():
    assert not is_coherent_payslip_total(7177.15, 695.81, 989.12, 1000.00)
