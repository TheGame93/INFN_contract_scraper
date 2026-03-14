"""Tests for the subtype normalizer."""

from infn_jobs.extract.parse.normalize.subtypes import normalize_subtype


def test_normalize_subtype_fascia_ii_to_fascia_2():
    assert normalize_subtype("Fascia II", 2015) == "Fascia 2"


def test_normalize_subtype_fascia_ii_case_insensitive():
    assert normalize_subtype("fascia ii", 2005) == "Fascia 2"


def test_normalize_subtype_fascia_iii_to_fascia_3():
    assert normalize_subtype("Fascia III", 2026) == "Fascia 3"


def test_normalize_subtype_fascia_arabic_to_same_level():
    assert normalize_subtype("Fascia 1", 2026) == "Fascia 1"


def test_normalize_subtype_tipo_a_post2010_to_junior():
    assert normalize_subtype("Tipo A", 2015) == "Junior"


def test_normalize_subtype_tipo_b_post2010_to_senior():
    assert normalize_subtype("Tipo B", 2012) == "Senior"


def test_normalize_subtype_tipo_a_pre2010_returns_none():
    assert normalize_subtype("Tipo A", 2008) is None


def test_normalize_subtype_tipo_a_anno_none_returns_none():
    assert normalize_subtype("Tipo A", None) is None


def test_normalize_subtype_none_input_returns_none():
    assert normalize_subtype(None, 2015) is None


def test_normalize_subtype_empty_returns_none():
    assert normalize_subtype("", 2015) is None


def test_normalize_subtype_junior_passthrough():
    assert normalize_subtype("junior", 2016) == "Junior"


def test_normalize_subtype_senior_passthrough():
    assert normalize_subtype("SENIOR", 2016) == "Senior"
