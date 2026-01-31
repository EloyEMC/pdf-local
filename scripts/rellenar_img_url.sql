-- Rellenar img_url a partir de imagen
-- Patrón: https://www.disano.it/_next/image/?url=https%3A%2F%2Fazprodmedia.blob.core.windows.net%2Fmediafiles%2Ffull_<imagen>&w=3840&q=75

BEGIN TRANSACTION;

UPDATE productos
SET img_url = 'https://www.disano.it/_next/image/?url=https%3A%2F%2Fazprodmedia.blob.core.windows.net%2Fmediafiles%2Ffull_' || imagen || '&w=3840&q=75'
WHERE imagen IS NOT NULL
  AND img_url IS NULL;

COMMIT;

-- Verificar resultados
SELECT
  'Actualizados' as metrica,
  COUNT(*) as valor
FROM productos
WHERE img_url LIKE 'https://www.disano.it/%'
  AND imagen IS NOT NULL;
