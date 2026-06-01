"""Catálogo de aeropuertos: orígenes en Colombia y destinos turísticos filtrados.

Estructura: {IATA: {"ciudad": str, "pais": str, "lat": float|None, "lon": float|None}}
Lista basada en el PLAN §1. Ajustable.
"""

# --- Orígenes: Colombia ---
ORIGENES = {
    "BOG": {"ciudad": "Bogotá", "pais": "Colombia", "lat": 4.7016, "lon": -74.1469},
    "MDE": {"ciudad": "Medellín", "pais": "Colombia", "lat": 6.1645, "lon": -75.4231},
    "CLO": {"ciudad": "Cali", "pais": "Colombia", "lat": 3.5432, "lon": -76.3816},
    "CTG": {"ciudad": "Cartagena", "pais": "Colombia", "lat": 10.4424, "lon": -75.5130},
    "BAQ": {"ciudad": "Barranquilla", "pais": "Colombia", "lat": 10.8896, "lon": -74.7808},
    "PEI": {"ciudad": "Pereira", "pais": "Colombia", "lat": 4.8128, "lon": -75.7395},
    "SMR": {"ciudad": "Santa Marta", "pais": "Colombia", "lat": 11.1196, "lon": -74.2306},
    "ADZ": {"ciudad": "San Andrés", "pais": "Colombia", "lat": 12.5836, "lon": -81.7112},
    "BGA": {"ciudad": "Bucaramanga", "pais": "Colombia", "lat": 7.1265, "lon": -73.1848},
    "CUC": {"ciudad": "Cúcuta", "pais": "Colombia", "lat": 7.9275, "lon": -72.5115},
    "MTR": {"ciudad": "Montería", "pais": "Colombia", "lat": 8.8237, "lon": -75.8258},
    "AXM": {"ciudad": "Armenia", "pais": "Colombia", "lat": 4.4528, "lon": -75.7664},
    "NVA": {"ciudad": "Neiva", "pais": "Colombia", "lat": 2.9500, "lon": -75.2940},
}

# --- Destinos: países de alta densidad turística (PLAN §1) ---
DESTINOS = {
    # LATAM
    "GRU": {"ciudad": "São Paulo", "pais": "Brasil", "lat": -23.4356, "lon": -46.4731},
    "GIG": {"ciudad": "Río de Janeiro", "pais": "Brasil", "lat": -22.8100, "lon": -43.2506},
    "SSA": {"ciudad": "Salvador", "pais": "Brasil", "lat": -12.9086, "lon": -38.3225},
    "REC": {"ciudad": "Recife", "pais": "Brasil", "lat": -8.1265, "lon": -34.9236},
    "FOR": {"ciudad": "Fortaleza", "pais": "Brasil", "lat": -3.7763, "lon": -38.5326},
    "SLZ": {"ciudad": "São Luís", "pais": "Brasil", "lat": -2.5853, "lon": -44.2341},
    "IGU": {"ciudad": "Foz de Iguazú", "pais": "Brasil", "lat": -25.5963, "lon": -54.4872},
    "FLN": {"ciudad": "Florianópolis", "pais": "Brasil", "lat": -27.6705, "lon": -48.5526},
    "CUN": {"ciudad": "Cancún", "pais": "México", "lat": 21.0365, "lon": -86.8771},
    "MEX": {"ciudad": "Ciudad de México", "pais": "México", "lat": 19.4363, "lon": -99.0721},
    "GDL": {"ciudad": "Guadalajara", "pais": "México", "lat": 20.5218, "lon": -103.3110},
    "LIM": {"ciudad": "Lima", "pais": "Perú", "lat": -12.0219, "lon": -77.1143},
    "CUZ": {"ciudad": "Cusco", "pais": "Perú", "lat": -13.5358, "lon": -71.9389},
    "EZE": {"ciudad": "Buenos Aires", "pais": "Argentina", "lat": -34.8222, "lon": -58.5358},
    "BRC": {"ciudad": "Bariloche", "pais": "Argentina", "lat": -41.1512, "lon": -71.1575},
    "SCL": {"ciudad": "Santiago", "pais": "Chile", "lat": -33.3930, "lon": -70.7858},
    "PTY": {"ciudad": "Ciudad de Panamá", "pais": "Panamá", "lat": 9.0714, "lon": -79.3835},
    "PUJ": {"ciudad": "Punta Cana", "pais": "Rep. Dominicana", "lat": 18.5674, "lon": -68.3634},
    "SDQ": {"ciudad": "Santo Domingo", "pais": "Rep. Dominicana", "lat": 18.4297, "lon": -69.6689},
    "SJO": {"ciudad": "San José", "pais": "Costa Rica", "lat": 9.9939, "lon": -84.2088},
    "HAV": {"ciudad": "La Habana", "pais": "Cuba", "lat": 22.9892, "lon": -82.4091},
    "VRA": {"ciudad": "Varadero", "pais": "Cuba", "lat": 23.0344, "lon": -81.4353},
    "MVD": {"ciudad": "Montevideo", "pais": "Uruguay", "lat": -34.8384, "lon": -56.0308},
    "UIO": {"ciudad": "Quito", "pais": "Ecuador", "lat": -0.1292, "lon": -78.3575},
    "GPS": {"ciudad": "Galápagos", "pais": "Ecuador", "lat": -0.4536, "lon": -90.2659},
    # Norteamérica
    "MIA": {"ciudad": "Miami", "pais": "EE. UU.", "lat": 25.7959, "lon": -80.2870},
    "MCO": {"ciudad": "Orlando", "pais": "EE. UU.", "lat": 28.4312, "lon": -81.3081},
    "JFK": {"ciudad": "Nueva York", "pais": "EE. UU.", "lat": 40.6413, "lon": -73.7781},
    "LAX": {"ciudad": "Los Ángeles", "pais": "EE. UU.", "lat": 33.9416, "lon": -118.4085},
    "LAS": {"ciudad": "Las Vegas", "pais": "EE. UU.", "lat": 36.0840, "lon": -115.1537},
    "YYZ": {"ciudad": "Toronto", "pais": "Canadá", "lat": 43.6777, "lon": -79.6248},
    "YUL": {"ciudad": "Montreal", "pais": "Canadá", "lat": 45.4706, "lon": -73.7408},
    # Europa
    "MAD": {"ciudad": "Madrid", "pais": "España", "lat": 40.4983, "lon": -3.5676},
    "BCN": {"ciudad": "Barcelona", "pais": "España", "lat": 41.2974, "lon": 2.0833},
    "CDG": {"ciudad": "París", "pais": "Francia", "lat": 49.0097, "lon": 2.5479},
    "FCO": {"ciudad": "Roma", "pais": "Italia", "lat": 41.8003, "lon": 12.2389},
    "MXP": {"ciudad": "Milán", "pais": "Italia", "lat": 45.6306, "lon": 8.7281},
    "VCE": {"ciudad": "Venecia", "pais": "Italia", "lat": 45.5053, "lon": 12.3519},
    "LHR": {"ciudad": "Londres", "pais": "Reino Unido", "lat": 51.4700, "lon": -0.4543},
    "LIS": {"ciudad": "Lisboa", "pais": "Portugal", "lat": 38.7742, "lon": -9.1342},
    "OPO": {"ciudad": "Oporto", "pais": "Portugal", "lat": 41.2481, "lon": -8.6814},
    "FRA": {"ciudad": "Fráncfort", "pais": "Alemania", "lat": 50.0379, "lon": 8.5622},
    "BER": {"ciudad": "Berlín", "pais": "Alemania", "lat": 52.3667, "lon": 13.5033},
    "AMS": {"ciudad": "Ámsterdam", "pais": "Países Bajos", "lat": 52.3105, "lon": 4.7683},
    # Mediterráneo / Medio Oriente
    "IST": {"ciudad": "Estambul", "pais": "Turquía", "lat": 41.2753, "lon": 28.7519},
    "AYT": {"ciudad": "Antalya", "pais": "Turquía", "lat": 36.8987, "lon": 30.8005},
    "CAI": {"ciudad": "El Cairo", "pais": "Egipto", "lat": 30.1219, "lon": 31.4056},
    "HRG": {"ciudad": "Hurghada", "pais": "Egipto", "lat": 27.1783, "lon": 33.7994},
    "SSH": {"ciudad": "Sharm el-Sheij", "pais": "Egipto", "lat": 27.9773, "lon": 34.3950},
    "LCA": {"ciudad": "Lárnaca", "pais": "Chipre", "lat": 34.8751, "lon": 33.6249},
    "ATH": {"ciudad": "Atenas", "pais": "Grecia", "lat": 37.9364, "lon": 23.9445},
    "JTR": {"ciudad": "Santorini", "pais": "Grecia", "lat": 36.3992, "lon": 25.4793},
    "TLV": {"ciudad": "Tel Aviv", "pais": "Israel", "lat": 32.0114, "lon": 34.8867},
    "AMM": {"ciudad": "Amán", "pais": "Jordania", "lat": 31.7226, "lon": 35.9932},
    "DXB": {"ciudad": "Dubái", "pais": "Emiratos", "lat": 25.2532, "lon": 55.3657},
    "AUH": {"ciudad": "Abu Dabi", "pais": "Emiratos", "lat": 24.4330, "lon": 54.6511},
    "DOH": {"ciudad": "Doha", "pais": "Qatar", "lat": 25.2731, "lon": 51.6080},
    "RAK": {"ciudad": "Marrakech", "pais": "Marruecos", "lat": 31.6069, "lon": -8.0363},
    "CMN": {"ciudad": "Casablanca", "pais": "Marruecos", "lat": 33.3675, "lon": -7.5898},
    "TUN": {"ciudad": "Túnez", "pais": "Túnez", "lat": 36.8510, "lon": 10.2272},
    # Asia / Oriente
    "NRT": {"ciudad": "Tokio (Narita)", "pais": "Japón", "lat": 35.7720, "lon": 140.3929},
    "HND": {"ciudad": "Tokio (Haneda)", "pais": "Japón", "lat": 35.5494, "lon": 139.7798},
    "KIX": {"ciudad": "Osaka", "pais": "Japón", "lat": 34.4347, "lon": 135.2440},
    "ICN": {"ciudad": "Seúl", "pais": "Corea del Sur", "lat": 37.4602, "lon": 126.4407},
    "PEK": {"ciudad": "Pekín", "pais": "China", "lat": 40.0799, "lon": 116.6031},
    "PVG": {"ciudad": "Shanghái", "pais": "China", "lat": 31.1443, "lon": 121.8083},
    "CAN": {"ciudad": "Cantón", "pais": "China", "lat": 23.3924, "lon": 113.2988},
    "HKG": {"ciudad": "Hong Kong", "pais": "Hong Kong", "lat": 22.3080, "lon": 113.9185},
    "BKK": {"ciudad": "Bangkok", "pais": "Tailandia", "lat": 13.6900, "lon": 100.7501},
    "HKT": {"ciudad": "Phuket", "pais": "Tailandia", "lat": 8.1132, "lon": 98.3169},
    "SGN": {"ciudad": "Ho Chi Minh", "pais": "Vietnam", "lat": 10.8188, "lon": 106.6520},
    "HAN": {"ciudad": "Hanói", "pais": "Vietnam", "lat": 21.2212, "lon": 105.8072},
    "SIN": {"ciudad": "Singapur", "pais": "Singapur", "lat": 1.3644, "lon": 103.9915},
    "DPS": {"ciudad": "Bali", "pais": "Indonesia", "lat": -8.7482, "lon": 115.1672},
    "CGK": {"ciudad": "Yakarta", "pais": "Indonesia", "lat": -6.1256, "lon": 106.6559},
    "DEL": {"ciudad": "Nueva Delhi", "pais": "India", "lat": 28.5562, "lon": 77.1000},
    "BOM": {"ciudad": "Bombay", "pais": "India", "lat": 19.0896, "lon": 72.8656},
    "KUL": {"ciudad": "Kuala Lumpur", "pais": "Malasia", "lat": 2.7456, "lon": 101.7099},
    "MNL": {"ciudad": "Manila", "pais": "Filipinas", "lat": 14.5086, "lon": 121.0194},
    "MLE": {"ciudad": "Maldivas", "pais": "Maldivas", "lat": 4.1918, "lon": 73.5291},
}

# Algunos destinos también pueden ser orígenes válidos (ciudades grandes),
# pero para Tracy el origen debe ser Colombia. Mantenemos los conjuntos separados.


def es_origen_valido(iata: str) -> bool:
    return bool(iata) and iata.strip().upper() in ORIGENES


def es_destino_valido(iata: str) -> bool:
    return bool(iata) and iata.strip().upper() in DESTINOS


def info(iata: str) -> dict | None:
    if not iata:
        return None
    iata = iata.strip().upper()
    return ORIGENES.get(iata) or DESTINOS.get(iata)


def nombre(iata: str) -> str:
    """Nombre legible de un aeropuerto: 'Ciudad' o el IATA si no se conoce."""
    datos = info(iata)
    if not datos:
        return (iata or "").strip().upper()
    return datos["ciudad"]


def pais(iata: str) -> str | None:
    datos = info(iata)
    return datos["pais"] if datos else None


def coords(iata: str) -> tuple[float, float] | None:
    datos = info(iata)
    if datos and datos.get("lat") is not None and datos.get("lon") is not None:
        return (datos["lat"], datos["lon"])
    return None
