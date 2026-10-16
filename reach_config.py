"""
ECHA REACH Candidate List & SCIP Data Dictionary
Compliant with WFD 2008/98/EC & REACH Regulation (EC) No 1907/2006 Art. 33
Judgment of the CJEU in Case C-106/14 ('Once an Article, Always an Article')
"""

# Yaygın BLDC Motor bileşenleri için Aday Liste (Candidate List) SVHC Maddeleri
SVHC_CANDIDATE_LIST = {
    "Lead": {
        "cas_number": "7439-92-1",
        "ec_number": "231-100-4",
        "reason_for_inclusion": "Toxic for reproduction (Article 57c)",
        "typical_material": "Metal / Brass / Bronze alloys",
        "safe_use_instructions": "No specific safe use advice required beyond general industrial hygiene."
    },
    "DEHP (Bis(2-ethylhexyl) phthalate)": {
        "cas_number": "117-81-7",
        "ec_number": "204-211-0",
        "reason_for_inclusion": "Toxic for reproduction (Article 57c)",
        "typical_material": "Flexible PVC / Cable insulation",
        "safe_use_instructions": "Do not swallow or ingest. Keep away from prolonged skin contact."
    },
    "D4 (Octamethylcyclotetrasiloxane)": {
        "cas_number": "556-67-2",
        "ec_number": "209-136-7",
        "reason_for_inclusion": "PBT & vPvB (Article 57d & 57e)",
        "typical_material": "Silicone seals / O-rings / Greases",
        "safe_use_instructions": "Avoid release to the aquatic environment. Dispose of as hazardous waste."
    },
    "Lead monoxide (Lead oxide)": {
        "cas_number": "1317-36-8",
        "ec_number": "215-267-0",
        "reason_for_inclusion": "Toxic for reproduction (Article 57c)",
        "typical_material": "Ceramic capacitors / Resistor glass matrices",
        "safe_use_instructions": "Do not dismantle or crush electronic components."
    }
}

# SCIP Eşikleri ve CN/TARIC Motor Kodları
SCIP_CONFIG = {
    "threshold_weight_percent": 0.1,  # %0.1 w/w
    "threshold_ppm": 1000.0,
    "complex_object_cn_code": "85013100",  # DC motors of an output <= 750 W
    "complex_object_name": "Brushless DC Motor Assembly (2.47 kg)"
}