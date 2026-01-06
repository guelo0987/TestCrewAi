# Pruebas de Estrés con Locust

Este directorio contiene las pruebas de estrés para la API usando Locust.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar Locust con interfaz web

```bash
locust -f main.py --host=http://127.0.0.1:8000
```

Luego abre tu navegador en: `http://localhost:8089`

### Ejecutar sin interfaz web (headless)

```bash
locust -f main.py --host=http://127.0.0.1:8000 --headless -u 100 -r 10 -t 60s
```

Parámetros:
- `-u 100`: 100 usuarios simultáneos
- `-r 10`: 10 usuarios por segundo (ramp-up rate)
- `-t 60s`: Duración de 60 segundos

### Ejecutar y guardar resultados

```bash
locust -f main.py --host=http://127.0.0.1:8000 --headless -u 100 -r 10 -t 60s --html report.html
```

## Endpoints Probados

1. **POST /auth/register** - Registro de usuarios (peso 3)
2. **POST /auth/login** - Login de usuarios (peso 5)
3. **GET /auth/me** - Obtener información del usuario actual (peso 2)

## Notas

- Asegúrate de que tu API esté corriendo antes de ejecutar las pruebas
- Los usuarios de prueba se generan automáticamente con emails aleatorios
- El script intenta mantener sesiones (login -> /me) cuando es posible

