# AIdeaText — Guía de Contexto para Claude Code
## Versión v2.0 · Abril 2026 · Autor: Manuel Vargas Alegría

> **PRINCIPIO DE TRABAJO:** Implementar el ShortTerm (piloto UNIFE) con decisiones de arquitectura que no cierren el camino al LongTerm. Cada decisión de código debe ser consciente de hacia dónde va el sistema.

---

## 🗺️ LOS DOS HORIZONTES

| | ShortTerm (AHORA) | LongTerm (FUTURO) |
|---|---|---|
| **Objetivo** | Piloto UNIFE — 1 profesora, ~10 tesistas | Plataforma global multi-institución |
| **Stack** | Streamlit + EC2 + DocumentDB | React/FastAPI + ECS Fargate + DynamoDB |
| **Usuarios** | Martha (profesora) + tesistas MG | UNIFE + OSU + Turquía + ... |
| **DB** | AWS DocumentDB (MongoDB) + SQLite | DynamoDB (índices) + S3 (objetos) |
| **Deploy** | `systemctl restart aideatext.service` | ECS autoscaling + 3 regiones AWS |
| **IA** | Claude API (Anthropic directo) | AWS Bedrock Claude Sonnet (15K TPM) |
| **Grafos** | NetworkX | NetworkX + cuGraph/GPU |
| **Métricas** | M1, M2, M1_D | M1, M2, M2_delta, four_way_coherence |

---

## 📁 ESTRUCTURA ACTUAL DEL PROYECTO (ShortTerm)

```
AIdeaText/
├── app.py                          # Entry point Streamlit
├── CLAUDE.md                       # Este archivo
├── AIdeaText_ShorTermScope.md      # Conversación Gemini — implementación actual
├── AIdeaText-GeneralVision-LongTermScope.md  # Blueprint largo plazo
│
├── modules/
│   ├── auth/
│   │   └── auth.py                 # bcrypt + SQLite para usuarios
│   ├── chatbot/
│   │   └── sidebar_chat.py         # Tutor virtual (sidebar Streamlit)
│   ├── database/
│   │   ├── semantic_mongo_db.py    # CRUD cubeta semantic_analysis
│   │   ├── chat_mongo_db.py        # CRUD cubeta chat_history-v3
│   │   └── discourse_mongo_db.py   # CRUD cubeta discourse_analysis
│   ├── metrics/
│   │   └── metrics_processor.py   # Calcula M1, M2, M1_D (Coherencia Dialógica)
│   ├── semantic/
│   │   └── semantic_process.py    # Pipeline NLP → grafo semántico
│   └── ui/
│       ├── user_page.py           # Interfaz del tesista
│       └── professor_ui.py        # Dashboard de Martha
│
├── scripts/                        # Scripts de migración/mantenimiento
│   ├── migrate_coherence_v3.py    # Migración de 4 cubetas con group_id
│   ├── populate_unife_demo.py     # Datos demo para Martha
│   └── delete_orphans.py          # Limpieza de datos con IDs incorrectos
│
└── requirements.txt
```

---

## 🗄️ BASE DE DATOS — ARQUITECTURA ACTUAL

### DocumentDB (MongoDB compatible)
**Endpoint:** `aideatext-documentdb-cluster.cluster-c1sowo2islad.us-east-2.docdb.amazonaws.com:27017`
**DB:** `aideatext`
**SSL:** Requiere `global-bundle.pem` + `tlsCAFile`

```python
# Conexión estándar — siempre usar este patrón
MONGO_URI = f"mongodb://{USER}:{PASS}@{ENDPOINT}:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
```

### Las 4 Cubetas (colecciones MongoDB)

| Cubeta | Descripción | Trigger | Modalidad LongTerm |
|--------|-------------|---------|-------------------|
| `student_semantic_live_analysis` | Análisis en tiempo real (pizarrón/live) | Estudiante escribe en live | W — Escritura |
| `student_semantic_analysis` | Análisis de documento Word/PDF (tesis) | Estudiante sube archivo | W — Escritura |
| `student_discourse_analysis` | Análisis de discurso | Actividad de discurso | V — Voz/Oral |
| `chat_history-v3` | Conversación con Tutor Virtual | Sesión de chat | T — Tutor Virtual |

**Regla crítica:** Todos los documentos DEBEN tener `group_id`. Sin este campo el sistema no puede asociar datos a grupos/cursos.

### SQL (SQLite/RDS)
- Gestión de usuarios y autenticación (bcrypt)
- Separado de MongoDB

---

## 🆔 JERARQUÍA DE IDs (CRÍTICO)

```
Formato completo estudiante: {PROF_INITIALS}-G{N}-{YEAR}-{PERIOD}-t{N}
Ejemplo:                      MG-G1-2025-1-t1

Donde:
  MG        = Iniciales del nombre completo de la profesora (Martha García → MG)
  G1        = Número de grupo (consecutivo, G1, G2, G3...)
  2025-1    = Año y período de conclusión del estudiante
  t1        = Código del tesista (t1, t2, t3...)

Group ID (sin tesista):   MG-G1-2025-1
Student Full ID:          MG-G1-2025-1-t1
```

**Lógica de parsing — SIEMPRE usar Right-to-Left:**
```python
parts = full_username.split('-')
if len(parts) >= 5:
    id_estudiante = parts[-1]          # Siempre el último: t1
    id_grupo = "-".join(parts[:-1])    # Todo lo anterior: MG-G1-2025-1
    display_grupo = f"Grupo {parts[1]} ({parts[2]}-{parts[3]})"  # Grupo G1 (2025-1)
```

⚠️ **NO usar** `parts[0:4]` (Left-to-Right) — falla porque el año tiene guión (`2025-1`).

---

## 📊 MÉTRICAS PRINCIPALES

| Métrica | Descripción | Rango | Fuente |
|---------|-------------|-------|--------|
| `M1` | Score de coherencia semántica | 0.0–1.0 | Cada cubeta |
| `M2` | Densidad del grafo conceptual | 0.0–1.0 | `concept_graph.M2_density` |
| `M1_D` | **Coherencia Dialógica** — promedio M1 de las 4 cubetas con penalización por varianza | 0.0–1.0 | Calculado en `metrics_processor.py` |

**Fórmula M1_D:**
```python
M1_D = mean(M1 por cubeta) * (1 - std(M1) * 0.15)
# La penalización de 0.15 baja el score si el estudiante es inconsistente
# entre lo que escribe y lo que dice en el chat
```

**Extracción de M2 — patrón robusto:**
```python
m2 = res.get('m2_score')  # Prioridad 1: campo directo
if m2 is None:
    cg = res.get('concept_graph', {})
    m2 = cg.get('M2_density') if isinstance(cg, dict) else 0.0
m2 = float(m2 or 0.0)
```

---

## 🖥️ INFRAESTRUCTURA AWS ACTUAL (ShortTerm)

```
EC2: ip-172-31-30-228 (us-east-2, Ohio)
User: ec2-user
App path: /home/ec2-user/app/
Virtualenv: /home/ec2-user/app/aideatextenv/
Service: aideatext.service (systemd)
Git branch activo: dev
```

**Comandos de operación:**
```bash
# Activar entorno
source /home/ec2-user/app/aideatextenv/bin/activate

# Reiniciar servicio
sudo systemctl restart aideatext.service

# Ver logs en tiempo real
sudo journalctl -u aideatext.service -f

# Ver estado
sudo systemctl status aideatext.service

# Git sync
cd /home/ec2-user/app && git pull origin dev
```

---

## 🤖 TUTOR VIRTUAL (Chatbot)

- Módulo: `modules/chatbot/sidebar_chat.py`
- Se llama desde `modules/ui/user_page.py`
- **Patrón de llamada correcto:**
  ```python
  # CORRECTO:
  display_sidebar_chat(lang_code, t.get('chatbot', {}))

  # INCORRECTO (causa error "chatbot_t no es dict"):
  display_sidebar_chat(lang_code, "algún_string")
  ```
- El historial se guarda en `chat_history-v3` en DocumentDB
- Formato de mensaje: `{'role': 'user'/'assistant', 'content': '...'}`

---

## 🔧 ERRORES CONOCIDOS Y SOLUCIONES

### Error 1: `chatbot_t no es dict, es <class 'str'>`
**Causa:** Se pasa un string en lugar del dict de traducciones al chatbot.
**Fix:** En `user_page.py` → `display_sidebar_chat(lang_code, t.get('chatbot', {}))`

### Error 2: `AttributeError: 'str' object has no attribute 'get'`
**Causa:** `analysis_result` llega como string en lugar de dict.
**Fix en `semantic_mongo_db.py`:**
```python
if isinstance(analysis_result, str):
    try:
        analysis_result = json.loads(analysis_result)
    except:
        logger.error("analysis_result llegó como string y no es JSON válido")
        return False
```

### Error 3: `Invalid salt` (bcrypt)
**Causa:** Hash de contraseña truncado o malformado en DB.
**Fix:** Actualizar contraseña del usuario de prueba directamente en DB. El campo debe tener mínimo 60 chars.

### Error 4: Grupos no aparecen en dashboard de Martha
**Causa:** `group_id` en MongoDB no coincide con `class_id` de la profesora.
**Fix:** Verificar que `group_id` sea `MG-G1-2025-1` (4 partes), no `MG-EDU-UNIFE-LIM` ni otro formato.

---

## 👩‍🏫 CONTEXTO DE USUARIO ACTUAL

**Martha (profesora):**
- `class_id` = `MG-G1-2025-1`
- Ve: Dashboard con tabs por grupo → por tesista → análisis individual
- Necesita: comparativa "Escritura vs. Diálogo" (M1_writing vs M1_chat)

**Tesistas activos:**
- `MG-G1-2025-1-t1`
- `MG-G1-2025-1-t2`

**Estado de datos en DB:**
- `student_semantic_analysis`: ~48 docs ✅
- `student_semantic_live_analysis`: ~1 doc ✅
- `student_discourse_analysis`: 0 docs (pendiente)
- `chat_history-v3`: 0 docs (pendiente)

---

## 🔭 REGLAS DE DISEÑO — SHORTTERM CON VISIÓN LONGTERM

> Estas reglas evitan deuda técnica que bloquee la migración futura:

1. **No hardcodear** endpoints de DB — siempre variables de entorno
2. **Separar queries de lógica** — los módulos `*_mongo_db.py` solo hacen CRUD
3. **`group_id` es obligatorio** en cada documento MongoDB — nunca insertar sin él
4. **`analysis_result` siempre es dict** — validar tipo antes de `.get()`
5. **Logs con `logger`**, nunca `print()` — para migrar a CloudWatch fácilmente
6. **ID format es inmutable** — `{PROF}-G{N}-{YEAR}-{PERIOD}-t{N}` debe sobrevivir el cambio de DB
7. **Las 4 cubetas son las 4 modalidades** — el concepto no cambia, solo el motor de storage
8. **M1/M2/M1_D son los nombres canónicos** — no renombrar en ShortTerm

---

## 🌍 LONGTERM — ARQUITECTURA OBJETIVO (Referencia)

### Multi-institución
| Institución | Estado | AWS Region |
|------------|--------|------------|
| UNIFE Lima, Perú | **Piloto activo 2026** | sa-east-1 |
| Ohio State (OSU) | Planificado | us-east-1 |
| Universidad Turca | Planificado | eu-central-1 |

### Pipelines de procesamiento objetivo
- **Pipeline A — NLP Graph:** ECS Fargate `c6g.xlarge`, SQS trigger, P95: 12s
- **Pipeline B — Whisper/Voz:** AWS Batch `g4dn.xlarge` GPU, P95: <5min
- **Pipeline C — Cross-modal:** AWS Lambda arm64, P95: 0.3s

### Schema objetivo (student_record v2.0)
- **W:** Escritura → `student_semantic_analysis`
- **T:** Tutor Virtual → `chat_history-v3`
- **V:** Voz/Oral → `student_discourse_analysis` (futuro: Whisper large-v3)
- **H:** Tutor Humano → Dyadic Interaction (pendiente)

---

## 📋 COMPLIANCE

| Dato | Retención | Restricción |
|------|-----------|-------------|
| Audio crudo | 30 días → eliminar | NUNCA cruzar regiones |
| Transcripciones | 5 años post-estudio | Solo anonimizadas cross-region |
| Grafos semánticos | 5 años post-estudio | Pueden cruzar regiones (anonimizados) |
| Consentimientos | PERMANENTE | Object Lock WORM |

**Marco legal activo:** Ley N° 29733 (Perú) · DS 016-2024-JUS
**Grade passthrough:** DESHABILITADO — los scores son investigación, no calificaciones oficiales

---

*CLAUDE.md v2.0 — Generado desde AIdeaText_ShorTermScope.md (260 turnos Gemini) + Blueprint LongTerm (docs A1–E3)*
*Autor: Manuel Vargas Alegría · mv@aideatext.com · Abril 2026*
