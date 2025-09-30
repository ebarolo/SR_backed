# Fix: "Attempt to overwrite 'module' in LogRecord"

## 🐛 Problema

Il sistema di logging mostrava il warning **"Attempt to overwrite 'module' in LogRecord"** invece dei veri errori. Questo accadeva perché alcuni campi custom avevano gli stessi nomi degli attributi nativi di `LogRecord`.

## ✅ Soluzione Applicata

### 1. **Rinominato campo `module` in `source_module`** (`cloud_logging_config.py`)
```python
# PRIMA
payload = {
    "module": record.module,  # ❌ Conflitto con attributo nativo
}

# DOPO
payload = {
    "source_module": record.module,  # ✅ Nessun conflitto
}
```

### 2. **Aggiunto `reserved_attrs` al JsonFormatter** (`cloud_logging_config.py`)
Specifica esplicitamente quali attributi nativi di LogRecord non devono essere sovrascritti:
```python
json_formatter = JsonFormatter(
    fmt="...",
    json_ensure_ascii=False,
    reserved_attrs=[
        'name', 'msg', 'args', 'created', 'filename', 'funcName',
        'levelname', 'levelno', 'lineno', 'module', 'msecs',
        'pathname', 'process', 'processName', 'thread', 'threadName',
        'exc_info', 'exc_text', 'stack_info', 'relativeCreated'
    ]
)
```

### 3. **Migliorato filtro campi extra** (`cloud_logging_config.py`)
Escluso esplicitamente gli attributi nativi quando si aggiungono campi extra:
```python
native_attrs = {
    'name', 'msg', 'args', 'created', 'filename', 'funcName',
    'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message',
    'pathname', 'process', 'processName', 'thread', 'threadName',
    'exc_info', 'exc_text', 'stack_info', 'relativeCreated'
}

for key, value in record.__dict__.items():
    if key not in native_attrs and not key.startswith('_'):
        if key not in payload:
            payload[key] = value
```

### 4. **Rinominato campo in error_handler.py**
```python
# PRIMA
"module": self.module_name,  # ❌ Potenziale conflitto

# DOPO
"error_module": self.module_name,  # ✅ Nome univoco
```

## 🧪 Come Verificare la Fix

### Test 1: Provocare un errore e verificare il log
```python
# In un endpoint qualsiasi (es. main.py)
@app.get("/test-error")
def test_error():
    try:
        raise ValueError("Questo è un test error!")
    except Exception as e:
        error_logger.log_exception("test_error", e, {"test": "context"})
        raise HTTPException(status_code=500, detail=str(e))
```

### Test 2: Verificare i log
```bash
# Controlla i log
tail -f logs/backend.jsonl

# Dovresti vedere:
# ✅ Il vero messaggio di errore
# ✅ "source_module" invece di "module"
# ✅ Nessun warning "Attempt to overwrite"
```

### Test 3: Log strutturato
```python
import logging
logger = logging.getLogger(__name__)

logger.error("Test error message", extra={
    "custom_field": "value",
    "request_id": "test-123"
})
```

## 📊 Campi Log Modificati

| Campo Vecchio | Campo Nuovo | Dove |
|--------------|-------------|------|
| `module` | `source_module` | cloud_logging_config.py (payload) |
| `module` | `error_module` | error_handler.py (extra context) |

## 🔍 Attributi Nativi di LogRecord

Per riferimento, questi sono gli attributi nativi che **NON** devono essere sovrascritti:
- `name`, `msg`, `args`, `created`
- `filename`, `funcName`, `levelname`, `levelno`
- `lineno`, `module`, `msecs`, `message`
- `pathname`, `process`, `processName`
- `thread`, `threadName`
- `exc_info`, `exc_text`, `stack_info`
- `relativeCreated`

## 📝 Note

- Le ricette già salvate **non sono influenzate**
- Il sistema continua a loggare normalmente, ma senza warning
- I vecchi log con "module" rimangono nei file esistenti
- I nuovi log useranno "source_module" e "error_module"

## 🚀 Riavvio Necessario

Per applicare le modifiche:
```bash
# Riavvia il server
# (Uvicorn rileva le modifiche automaticamente in dev mode)
```

## ✨ Benefici

- ✅ Nessun più warning "Attempt to overwrite"
- ✅ I veri errori sono ora visibili
- ✅ Log più puliti e leggibili
- ✅ Compatibilità con Google Cloud Logging
- ✅ Migliore debugging

