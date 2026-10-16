"""
Multi-Regional Regulatory Configuration Database
Supports: EU (RoHS 2.0), US (TSCA & Prop 65), CHINA (China RoHS), and GLOBAL AUDIT.
"""

REGULATORY_PROFILES = {
    "EU": {
        "region_name": "European Union (EU)",
        "directives": ["RoHS 2.0 (Directive 2011/65/EU)", "Amending Directive (EU) 2015/863"],
        "limits_ppm": {
            "Lead": 1000,
            "Cadmium": 100,
            "Mercury": 1000
        },
        "exemptions_supported": {
            "Exemption 6(c)": {
                "material": "Brass",
                "element": "Lead",
                "max_ppm": 40000,  # 4% lead in copper alloys
                "description": "Lead as an alloying element in copper containing up to 4% lead by weight"
            }
        },
        "mandatory_mark": "CE Mark + SCIP Dossier"
    },
    "US": {
        "region_name": "United States (US - Federal & California)",
        "directives": ["US EPA TSCA Title VI", "California Proposition 65"],
        "limits_ppm": {
            "Lead": 800,       # Stricter safe harbor enforcement under Prop 65 consumer warnings
            "Cadmium": 100,
            "Mercury": 1000
        },
        "exemptions_supported": {}, # US Prop 65 typically requires warning labels rather than blanket exemptions
        "mandatory_mark": "Prop 65 Warning Label (if Pb > 800 ppm without consumer barrier)"
    },
    "CHINA": {
        "region_name": "People's Republic of China (China RoHS)",
        "directives": ["MIIT Management Methods / SJ/T 11364-2014", "GB/T 26572-2011"],
        "limits_ppm": {
            "Lead": 1000,
            "Cadmium": 100,
            "Mercury": 1000
        },
        "exemptions_supported": {
            "Exemption 6(c)": {
                "material": "Brass",
                "element": "Lead",
                "max_ppm": 40000,
                "description": "Copper alloy machining exemption"
            }
        },
        "mandatory_mark": "EFUP (Environment-Friendly Use Period - 20 Years Logo)"
    }
}