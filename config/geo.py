COMMON_GEO_DATA = {
    "Latam": [
        "Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Costa Rica", "Cuba",
        "Ecuador", "El Salvador", "Guatemala", "Honduras", "México", "Nicaragua",
        "Panamá", "Paraguay", "Perú", "Puerto Rico", "República Dominicana", "Uruguay", "Venezuela"
    ],
    "Norte América": [
        "Estados Unidos", "Canadá", "México"
    ],
    "Europa": [
        "Alemania", "España", "Francia", "Italia", "Reino Unido", "Países Bajos", "Suiza", "Portugal"
    ],
    "Asia": [
        "India", "Singapur", "Japón", "China", "Corea del Sur"
    ],
    "África": [
        "Sudáfrica", "Nigeria", "Kenia", "Egipto"
    ],
    "Oceanía": [
        "Australia", "Nueva Zelanda"
    ]
}

# Mapping date ranges to LinkedIn's f_TPR parameter
# Note: LinkedIn's guest API doesn't support arbitrary date ranges,
# so we map to the closest available option.
LINKEDIN_TPR_MAP = {
    "past 24 hours": "r86400",
    "past week": "r604800",
    "past month": "r2592000",
    "past year": "r31536000", # approximation, not always available directly
    "any time": "" # default for no specific filter
}
