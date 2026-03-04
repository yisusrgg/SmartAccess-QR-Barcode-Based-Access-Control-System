import json
import requests
import html 
from django.contrib.auth.backends import ModelBackend
from .models import Usuario
from alumno.models import Alumno
from credenciales.models import Credencial

class SicenetAuthBackend(ModelBackend):
    base_url = "https://sicenet.surguanajuato.tecnm.mx/ws/wsalumnos.asmx"
    
    def extraer_json(self, texto, etiqueta):
        etiqueta_inicio = f"<{etiqueta}>"
        etiqueta_fin = f"</{etiqueta}>"
        
        if etiqueta_inicio not in texto:
            return None
            
        inicio = texto.find(etiqueta_inicio) + len(etiqueta_inicio)
        fin = texto.find(etiqueta_fin)
        resultado_interno = texto[inicio:fin]
        
        json_limpio = html.unescape(resultado_interno)
        
        try:
            return json.loads(json_limpio)
        except json.JSONDecodeError:
            print(f"Error decodificando el JSON de {etiqueta}.")
            return None

   
    def crear_peticion_soap(self, operacion, cuerpo_xml=""):
        xml_data = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">\n'
            '  <soap:Body>\n'
            f'    <{operacion} xmlns="http://tempuri.org/">\n'
            f'      {cuerpo_xml}\n'
            f'    </{operacion}>\n'
            '  </soap:Body>\n'
            '</soap:Envelope>'
        )
        cuerpo_bytes = xml_data.encode('utf-8')
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': f'"http://tempuri.org/{operacion}"',
            'Content-Length': str(len(cuerpo_bytes))
        }
        return cuerpo_bytes, headers

    
    def validar_login_sicenet(self, username, password):
        try:
            # Conseguir  las cookies
            sesion = requests.Session()
            sesion.get(self.base_url, timeout=10) 
            
            # Iniciar Sesión
            cuerpo_login = f'<strMatricula>{username}</strMatricula>\n<strContrasenia>{password}</strContrasenia>\n<tipoUsuario>ALUMNO</tipoUsuario>'
            bytes_login, headers_login = self.crear_peticion_soap("accesoLogin", cuerpo_login)
            respuesta_login = sesion.post(self.base_url, data=bytes_login, headers=headers_login, timeout=10)
            datos_login = self.extraer_json(respuesta_login.text, "accesoLoginResult")
            
            # Si el login falla o no hay datos, salimos de inmediato
            if not datos_login or datos_login.get("acceso") != True:
                return None
                
            # Obtener Datos Académicos 
            bytes_datos, headers_datos = self.crear_peticion_soap("getAlumnoAcademicoWithLineamiento")
            respuesta_datos = sesion.post(self.base_url, data=bytes_datos, headers=headers_datos, timeout=10)
            datos_academicos = self.extraer_json(respuesta_datos.text, "getAlumnoAcademicoWithLineamientoResult")
            
            print(f"Datos académicos: {datos_academicos}")
            return datos_academicos
                
        except Exception as e:
            print(f"Error conectando a SICENET: {e}")
            return None
        

    # --- AUTENTICACIÓN DJANGO ---
    def authenticate(self, request, username=None, password=None, **kwargs):    
        datos_alumno = self.validar_login_sicenet(username, password)

        if datos_alumno is not None:
            carrera = datos_alumno.get("carrera", "")
            semestre = datos_alumno.get("semActual", "") 
            nombre_completo = datos_alumno.get("nombre", "")
            #sacar lastname con los ultimos dos nombres del campo nombre_completo
            nombre_completo = nombre_completo.split()
            if len(nombre_completo) >= 2:
                apellido_paterno = nombre_completo[-2]
                apellido_materno = nombre_completo[-1]
            else:
                apellido_paterno = ""
                apellido_materno = ""
            #el resto del nombre  
            nombre = nombre_completo[:-2] if len(nombre_completo) > 2 else nombre_completo
            nombre = " ".join(nombre)
            print("Nombre separado", nombre, apellido_paterno, apellido_materno)
            
            try:
                # Si el usuario ya existe, lo usamos
                usuario = Usuario.objects.get(username=username)
            except Usuario.DoesNotExist:
                # Si es la primera vez que entra a tu sistema, lo creamos
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=f"{username}@alumnos.itsur.edu.mx",
                    password=None,
                    first_name=nombre,
                    last_name=f"{apellido_paterno} {apellido_materno}"
                )
                
                Alumno.objects.create(
                    usuario=usuario,
                    matricula=username,
                    semestre=semestre,
                    carrera=carrera
                )

                Credencial.objects.create(usuario=usuario, fecha_expiracion="2026-12-31")
            
            return usuario
        
        return None