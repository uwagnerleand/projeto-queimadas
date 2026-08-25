# Instalação das Dependências Geoespaciais

## Para Windows (Recomendado):
```bash
# Usando conda (mais fácil)
conda install geopandas

# Ou via pip com wheels pré-compiladas
pip install geopandas shapely
```

## Para Linux/Mac:
```bash
pip install geopandas shapely fiona pyogrio
```

## Verificação:
```python
import geopandas as gpd
from shapely.geometry import Point

print("GeoPandas instalado com sucesso!")
```

## Problemas Comuns:
- **Windows + Fiona**: Use `conda install geopandas` ao invés de pip
- **GDAL não encontrado**: Instale GDAL via conda primeiro
- **Versões incompatíveis**: Use Python 3.8-3.11 para melhor compatibilidade

## Dependências do Sistema:
- GDAL (>= 3.0)
- PROJ (>= 6.0)
- GEOS (>= 3.8)