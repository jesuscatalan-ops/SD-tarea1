import pandas as pd

df = pd.read_csv("datos/967_buildings.csv")

lat_min = -33.530
lat_max = -33.390
lon_min = -70.810
lon_max = -70.550

filtro = (
    (df["latitude"] >= lat_min) & (df["latitude"] <= lat_max) &
    (df["longitude"] >= lon_min) & (df["longitude"] <= lon_max)
)

df_filtrado = df[filtro]
print(f"Edificios encontrados: {len(df_filtrado)}")
df_filtrado.to_csv("datos/dataset.csv", index=False)
print("✅ dataset.csv guardado")