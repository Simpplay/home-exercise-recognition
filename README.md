# Clasificación de Ejercicios Físicos con YOLO

Proyecto final — Visión Artificial, Universidad Nacional de Colombia.
Clasifica **10 ejercicios físicos domésticos** (Chair_Dip, Estiramiento_lateral,
Forward_Lunge, High_Knees, Jumping_Jack, Plank, Push-up, Sit-up, Squat,
Superman) a partir de una imagen de cuerpo completo, usando un clasificador
**YOLO11n-cls** (Ultralytics).

## Resultado

**85.35% de accuracy** (F1 macro 0.84) sobre una persona nunca vista en
entrenamiento ni validación, con un ensemble de 3 modelos YOLO11n-cls
idénticos entrenados con distinta semilla. Historial completo de
experimentos en [`experimentos.csv`](experimentos.csv) y análisis detallado
en las secciones 6 y 11 del notebook.

## Cómo ejecutar (Google Colab)

El dataset (fotos de las personas que grabaron los ejercicios) **no está en
este repositorio** por privacidad — vive en Google Drive.

1. Abre `Proyecto_Final_Vision.ipynb` en Colab.
2. Sube tu carpeta `dataset/` a Google Drive con la estructura
   `dataset/personaXX/<Clase>/*.png`.
3. Ejecuta la sección 1 del notebook: clona este repo, instala dependencias
   y monta tu Drive.
4. Corre el resto de celdas en orden. Por defecto (`EJECUTAR_ENTRENAMIENTO =
   False`) no reentrena: carga directamente los pesos ya entrenados en
   [`modelos_finales/`](modelos_finales) y evalúa/demuestra el ensemble final.

## Estructura del repo

- `Proyecto_Final_Vision.ipynb` — pipeline completo: exploración del
  dataset, construcción del split, augmentation, entrenamiento, evaluación,
  análisis de errores y demo en vivo.
- `modelos_finales/` — pesos de los 3 modelos que forman el ensemble final
  (~3 MB c/u).
- `experimentos.csv` — registro de todos los experimentos corridos (31 a la
  fecha), con hiperparámetros, split usado y métricas.
- `dataset/`, `dataset_cls/`, `runs_cls/` — no están en git (dataset por
  privacidad; los otros dos se regeneran al ejecutar el notebook).

## Restricción de diseño

El pipeline es **YOLO puro de punta a punta** (sin HOG/SVM ni un pipeline
clásico de segmentación + extracción de características + clasificador por
separado): el backbone convolucional aprende ambas cosas end-to-end. La
sección 3.5 del notebook justifica esta decisión con evidencia experimental.
