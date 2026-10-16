import pytest
from reach_config import SCIP_CONFIG

def assess_svhc_at_article_level(article_mass_g, svhc_mass_g, product_mass_g):
    """
    CJEU C-106/14 içtihadına uygun SCIP değerlendirme fonksiyonu.
    Konsantrasyon ürün kütlesine DEĞİL, artikel kütlesine bölünür.
    """
    if article_mass_g <= 0:
        raise ValueError("Article mass must be strictly positive.")

    article_conc_pct = (svhc_mass_g / article_mass_g) * 100.0
    diluted_product_conc_pct = (svhc_mass_g / product_mass_g) * 100.0

    scip_required = article_conc_pct > SCIP_CONFIG['threshold_weight_percent']

    return {
        "article_conc_pct": article_conc_pct,
        "diluted_product_conc_pct": diluted_product_conc_pct,
        "scip_required": scip_required,
        "rule_id": "SCIP_SVHC_THRESHOLD"
    }

def test_svhc_article_concentration_not_diluted_by_product_mass():
    """
    Örnek: 100 g artikelde 0.2 g Kurşun var.
    Artikel konsantrasyonu: 0.2 / 100 = %0.20 w/w (> %0.1 -> SCIP MANDATORY).
    2500 g motora bölünürse seyreltme (dilution) yapıp %0.008 çıkararak hata vermesini engelliyoruz.
    """
    article_mass = 100.0   # g
    svhc_mass = 0.2        # g
    product_mass = 2500.0  # g

    result = assess_svhc_at_article_level(
        article_mass_g=article_mass,
        svhc_mass_g=svhc_mass,
        product_mass_g=product_mass
    )

    assert result["scip_required"] is True
    assert result["article_conc_pct"] == 0.2
    assert result["diluted_product_conc_pct"] < SCIP_CONFIG['threshold_weight_percent']
    assert result["rule_id"] == "SCIP_SVHC_THRESHOLD"

def test_svhc_below_threshold_is_exempt():
    """Eşik altındaki (%0.025 w/w) artikeller SCIP bildiriminden muaf olmalıdır."""
    article_mass = 200.0
    svhc_mass = 0.05
    product_mass = 2500.0

    result = assess_svhc_at_article_level(article_mass, svhc_mass, product_mass)
    assert result["scip_required"] is False