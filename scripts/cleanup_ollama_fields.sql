-- Script para eliminar campos obsoletos de Ollama
-- Ejecutar con: sqlite3 database/tarifa_disano.db < scripts/cleanup_ollama_fields.sql

BEGIN TRANSACTION;

-- Crear tabla nueva sin campos obsoletos
CREATE TABLE productos_new (
    MARCA TEXT,
    "CÓDIGO" TEXT PRIMARY KEY,
    "CÓDIGO WEB" TEXT,
    REFERENCIA TEXT,
    "EAN 13" REAL,
    DESCRIPCION TEXT,
    "U.P.LOG" REAL,
    "U.CAJA" INTEGER,
    "DTO." TEXT,
    "CLASE ETIM" TEXT,
    RAEE_A REAL,
    RAEE_L REAL,
    RAEE_T REAL,
    "Peso bruto KG" REAL,
    "Peso bruto GR" REAL,
    "Peso neto KG" REAL,
    "Peso neto GR" REAL,
    "Longitud M" REAL,
    "Longitud MM" REAL,
    "Ancho M" REAL,
    "Ancho MM" REAL,
    "Alto M" REAL,
    "Altura MM" REAL,
    "Volumen DM3" REAL,
    CM3 REAL,
    Serie_familia_1 TEXT,
    Familia_WEB TEXT,
    Familia_Catalogo TEXT,
    Familia_Catalogo_PTL TEXT,
    imagen TEXT,
    Url_ficha_tec TEXT,
    descontinuado INTEGER,
    descripcion_corta TEXT,
    enlace_descarga TEXT,
    img_url TEXT,
    texto_extraido TEXT,
    texto_raw TEXT,
    "PVP_26_01_26" REAL,
    bc3_descripcion_corta TEXT,
    bc3_descripcion_larga TEXT,
    bc3_product_type TEXT,
    bc3_processed_at TIMESTAMP,
    bc3_model TEXT
);

-- Insertar datos excluyendo campos obsoletos
INSERT INTO productos_new
SELECT
    MARCA,
    "CÓDIGO",
    "CÓDIGO WEB",
    REFERENCIA,
    "EAN 13",
    DESCRIPCION,
    "U.P.LOG",
    "U.CAJA",
    "DTO.",
    "CLASE ETIM",
    RAEE_A,
    RAEE_L,
    RAEE_T,
    "Peso bruto KG",
    "Peso bruto GR",
    "Peso neto KG",
    "Peso neto GR",
    "Longitud M",
    "Longitud MM",
    "Ancho M",
    "Ancho MM",
    "Alto M",
    "Altura MM",
    "Volumen DM3",
    CM3,
    Serie_familia_1,
    Familia_WEB,
    Familia_Catalogo,
    Familia_Catalogo_PTL,
    imagen,
    Url_ficha_tec,
    descontinuado,
    descripcion_corta,
    enlace_descarga,
    img_url,
    texto_extraido,
    texto_raw,
    "PVP_26_01_26",
    bc3_descripcion_corta,
    bc3_descripcion_larga,
    bc3_product_type,
    bc3_processed_at,
    bc3_model
FROM productos;

-- Eliminar tabla vieja
DROP TABLE productos;

-- Renombrar tabla nueva
ALTER TABLE productos_new RENAME TO productos;

-- Recrear índices
CREATE INDEX IF NOT EXISTS idx_marca ON productos(MARCA);
CREATE INDEX IF NOT EXISTS idx_descontinuado ON productos(descontinuado);
CREATE INDEX IF NOT EXISTS idx_familia_web ON productos(Familia_WEB);
CREATE INDEX IF NOT EXISTS idx_codigo_web ON productos("CÓDIGO WEB");
CREATE INDEX IF NOT EXISTS idx_enlace_descarga ON productos(enlace_descarga);
CREATE INDEX IF NOT EXISTS idx_img_url ON productos(img_url);
CREATE INDEX IF NOT EXISTS idx_texto_extraido ON productos(texto_extraido);

COMMIT;

-- Verificar
.schema productos
