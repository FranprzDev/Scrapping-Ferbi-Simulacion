# Scrapping-Ferbi-Simulacion

Scraping estatico de celulares en Ferbi para obtener **1 fila por modelo** y facilitar comparacion con datasets tipo GSMArena.

## Fuente

- https://ferbi.com.ar/shop/category/celulares-38
- https://ferbi.com.ar/shop/category/celulares-38/page/2

## Salida

- `dataset/ferbi_celulares_modelos.csv`

El CSV se conserva en el repo y es el artefacto principal para comparar.

## Como ejecutar

1. Instalar dependencias:

```bash
pip install requests beautifulsoup4
```

2. Ejecutar:

```bash
python scraper_ferbi_modelos.py
```

3. Resultado:

- Se genera/actualiza `dataset/ferbi_celulares_modelos.csv`.

## Criterio de modelado

- **1 fila por modelo** (sin expansion cartesiana de variantes).
- Campos multivalor serializados con `|` (por ejemplo `status`, `storage_options_gb`, `ferbi_colores`).
- Validacion de enum para condicion de equipo (`Como Nuevo | Re Bueno | Bueno`) en `ferbi_condicion_enum_ok`.

## Columnas principales

- `phone_id`, `phone_name`, `phone_url`
- `status` (condiciones disponibles, separadas por `|`)
- `storage_options_gb`
- `ferbi_colores`, `ferbi_marcas`
- `ferbi_attributes_json` (atributos crudos extraidos)

## Nota

El scraping es estatico (HTTP + parseo HTML), sin navegador.
