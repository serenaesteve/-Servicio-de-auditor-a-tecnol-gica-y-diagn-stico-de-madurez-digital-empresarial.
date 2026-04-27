# DigiAudit — Diagnóstico de madurez digital empresarial

App Flask para realizar auditorías tecnológicas y diagnósticos de madurez digital.

## Instalación y uso

```bash
pip install flask
python app.py
```

Accede en: http://localhost:5000

## Credenciales demo
- Email: admin@digiaudit.com
- Contraseña: admin123

## Funcionalidades

- **Login / Registro** de auditores
- **Gestión de empresas** (sector, tamaño, contacto)
- **Auditorías por 6 dimensiones**:
  - Estrategia digital
  - Datos y analítica
  - Infraestructura tecnológica
  - Experiencia de cliente
  - Operaciones y procesos
  - Talento y cultura digital
- **5 preguntas por dimensión** con escala 1–5
- **Autoguardado** mientras completas el formulario
- **Panel de resultados** con índice global, nivel de madurez y plan de acción
- **Panel de admin** con vista global de todas las auditorías y usuarios

## Niveles de madurez
| Score | Nivel |
|-------|-------|
| < 36% | Inicial |
| 36–52% | Básico |
| 52–68% | Definido |
| 68–84% | Avanzado |
| > 84% | Líder |
