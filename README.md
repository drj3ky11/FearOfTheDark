# FearOfTheDark

Repositorio académico para el análisis de datos filtrados de grupos de ransomware y foros de hacking mediante LLMs en local (Ollama).

> Material desarrollado para uso en entornos de máster e investigación en ciberseguridad.

---

## Módulos

| Módulo | Descripción | Estado | Notebooks |
|---|---|---|---|
| [`ContiLeaks/`](ContiLeaks/) | Análisis de los chats internos filtrados del grupo Conti (2020–2022) | ✅ Completo | 00 extracción · 01 carga/limpieza · 02 LLM · 03 embeddings |
| [`BlackBasta/`](BlackBasta/) | Análisis de los chats filtrados de Black Basta (2023–2024) | ✅ Completo | 00 exploración · 01 carga/limpieza · 02 LLM · 03 embeddings |
| [`LockBit/`](LockBit/) | Análisis del panel dump de LockBit (dic 2024 – abr 2025) | 🔄 En ejecución | 00 extracción · 01 operacional · 02 LLM · 03 embeddings · 04 analista conversacional |

### Análisis comparativo

| Notebook | Descripción |
|---|---|
| [`comparative/01_cross_group_similarity.ipynb`](comparative/01_cross_group_similarity.ipynb) | Similitud semántica cruzada Conti ↔ Black Basta: centroides de actores, heatmap, UMAP conjunto, cohesión intra vs inter-grupo |

### Guión de taller

[`GUION_TALLER.md`](GUION_TALLER.md) — documentación completa del proceso, cifras de los datasets, puntos de discusión y apéndice técnico. Sirve como guión para sesiones de 4–5 horas.

---

## Dataset

Los datos de origen se distribuyen fuera del repositorio por razones éticas y de tamaño. Se proporciona acceso por vías alternativas a los alumnos.

Estructura esperada en local:

```
FearOfTheDark/
└── data_bruto/          ← no incluido en el repo (.gitignore)
    └── Ransomware/
        ├── BlackBasta-Chats-main/
        ├── Conti_Chats_2022.zip
        └── Lockbit_paneldb_dump 2025.zip
```

---

## Requisitos generales

- Python 3.10+
- [Ollama](https://ollama.com) corriendo en local
- `p7zip-full` para descomprimir archivos `.7z`

```bash
sudo apt install p7zip-full
ollama pull qwen2.5:14b
ollama pull nomic-embed-text-v2-moe
```

---

## Ética y uso responsable

Este material se distribuye exclusivamente con fines académicos y de threat intelligence. Los datasets utilizados son leaks públicamente documentados por investigadores de seguridad (PRODAFT, VXUnderground). Queda prohibido:

- Redistribuir los datos originales
- Intentar descifrar hashes presentes en los dumps
- Usar la infraestructura identificada (C2, BTC) para ningún propósito

---

## Licencia

[Creative Commons BY-NC-SA 4.0](LICENSE) — libre para uso académico y educativo, sin fines comerciales, con atribución.
