from locust import HttpUser, task, between
import random
import string


class APIUser(HttpUser):
    """
    Clase de usuario para pruebas de estrés con Locust
    Prueba los endpoints de autenticación de la API
    """
    wait_time = between(1, 3)  # Espera entre 1 y 3 segundos entre requests
    
    def on_start(self):
        """Se ejecuta cuando un usuario inicia una sesión de prueba"""
        self.token = None
        self.correo = None
        self.password = None
        
    def generate_random_string(self, length=10):
        """Genera una cadena aleatoria"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def generate_random_email(self):
        """Genera un email aleatorio"""
        return f"test_{self.generate_random_string(8)}@example.com"
    
    @task(3)
    def register_user(self):
        """Prueba el endpoint de registro (peso 3 - más frecuente)"""
        correo = self.generate_random_email()
        nombre = f"Usuario {self.generate_random_string(5)}"
        password = "testpassword123"
        
        empresa_data = {
            "nombre": f"Empresa {self.generate_random_string(6)}",
            "descripcion": "Empresa de prueba",
            "logo_url": None,
            "colores_marca": None
        }
        
        payload = {
            "correo": correo,
            "nombre": nombre,
            "password": password,
            "empresa": empresa_data
        }
        
        with self.client.post(
            "/auth/register",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
                # Guardar credenciales para login posterior
                self.correo = correo
                self.password = password
            elif response.status_code == 400:
                # Puede fallar si el correo ya existe (en pruebas concurrentes)
                response.failure("Correo ya existe o datos inválidos")
            else:
                response.failure(f"Error inesperado: {response.status_code}")
    
    @task(10)
    def login_user(self):
        """Prueba el endpoint de login (peso 10 - enfocado en login)"""
        # Usar credenciales de prueba - CAMBIA ESTOS VALORES POR TUS CREDENCIALES REALES
        correo = "miguel@example.com"  # ⚠️ CAMBIA ESTO por un correo real de tu BD
        password = "1304"  # ⚠️ CAMBIA ESTO por la contraseña real
        
        payload = {
            "correo": correo,
            "password": password
        }
        
        with self.client.post(
            "/auth/login",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                # Guardar el token para usar en /me
                data = response.json()
                self.token = data.get("access_token")
            elif response.status_code == 401:
                response.failure("Credenciales incorrectas")
            else:
                response.failure(f"Error inesperado: {response.status_code}")
    
    @task(2)
    def get_current_user(self):
        """Prueba el endpoint /me (peso 2 - menos frecuente)"""
        if not self.token:
            # Intentar hacer login primero
            self.login_user()
        
        if self.token:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            
            with self.client.get(
                "/auth/me",
                headers=headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 401:
                    response.failure("Token inválido o expirado")
                    self.token = None  # Resetear token
                else:
                    response.failure(f"Error inesperado: {response.status_code}")

