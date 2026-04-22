from datetime import datetime, timedelta
import json
import requests
import html 
from django.utils import timezone
from django.contrib.auth.backends import ModelBackend
from .models import Usuario
from alumno.models import Alumno
from personal.models import Personal
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

    
    def validar_login_sicenet(self, username, password, tipo):
        try:
            # Conseguir  las cookies
            sesion = requests.Session()
            sesion.get(self.base_url, timeout=10) 
            
            # Iniciar Sesión
            cuerpo_login = f'<strMatricula>{username}</strMatricula>\n<strContrasenia>{password}</strContrasenia>\n<tipoUsuario>{tipo}</tipoUsuario>'
            bytes_login, headers_login = self.crear_peticion_soap("accesoLogin", cuerpo_login)
            respuesta_login = sesion.post(self.base_url, data=bytes_login, headers=headers_login, timeout=10)
            datos_login = self.extraer_json(respuesta_login.text, "accesoLoginResult")

            print(f"Respuesta login: {datos_login}")
            
            # Si el login falla o no hay datos, salimos de inmediato
            if not datos_login or datos_login.get("acceso") != True:
                return None
            
            if datos_login.get("tipoUsuario") == 0:
                # Obtener Datos Académicos 
                bytes_datos, headers_datos = self.crear_peticion_soap("getAlumnoAcademicoWithLineamiento")
                respuesta_datos = sesion.post(self.base_url, data=bytes_datos, headers=headers_datos, timeout=10)
                datos_academicos = self.extraer_json(respuesta_datos.text, "getAlumnoAcademicoWithLineamientoResult")

                print(f"Datos académicos: {datos_academicos}")
                return datos_academicos

            if datos_login.get("tipoUsuario") == 1:
                #print(f"Datos académicos: {datos_academicos}")
                return datos_login
                
        except Exception as e:
            print(f"Error conectando a SICENET: {e}")
            return None
        

    # --- AUTENTICACIÓN DJANGO ---
    def authenticate(self, request, username=None, password=None, **kwargs):  
        tipo = kwargs.get('tipo', "ALUMNO") 
        tipo = "ALUMNO" if tipo in ["0", "ALUMNO"] else "DOCENTE"
        datos = self.validar_login_sicenet(username, password, tipo)

        if datos is not None:
            carrera = datos.get("carrera", "")
            semestre = datos.get("semActual", "") 
            nombre_completo = datos.get("nombre", username)
            estado_credencial = datos.get("estatus", False)
            print(f"Datos obtenidos de SICENET: {estado_credencial}")
            if isinstance(estado_credencial, str) and (estado_credencial.upper() == "VIGENTE" or estado_credencial.upper() == "VI"):
                estado_credencial = True
            else:
                estado_credencial = False

            print(f"Datos obtenidos de SICENET: {estado_credencial}")

            #sacar lastname con los ultimos dos nombres del campo nombre_completo
            if isinstance(nombre_completo, str) and nombre_completo.strip():
                partes = nombre_completo.split()
                if len(partes) >= 2:
                    apellido_paterno = partes[-2]
                    apellido_materno = partes[-1]
                    nombre = " ".join(partes[:-2]) if len(partes) > 2 else partes[0]
                else:
                    nombre = nombre_completo
                    apellido_paterno = ""
                    apellido_materno = ""
            else:
                nombre = username
                apellido_paterno = ""
                apellido_materno = ""
            print("Nombre separado", nombre, apellido_paterno, apellido_materno)
            
            try:
                # Si el usuario ya existe, lo usamos
                usuario = Usuario.objects.get(username=username)
            except Usuario.DoesNotExist:
                # Si es la primera vez que entra a tu sistema, lo creamos
                extension_correo = "alumnos.itsur.edu.mx" if tipo == "ALUMNO" else "itsur.edu.mx"
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=f"{username}@{extension_correo}",
                    password=None,
                    first_name=nombre,
                    last_name=f"{apellido_paterno} {apellido_materno}"
                )

                if tipo == "ALUMNO" or tipo == "0":
                    Alumno.objects.create(
                        usuario=usuario,
                        matricula=username,
                        semestre=semestre,
                        carrera=carrera
                    )
                elif tipo == "DOCENTE" or tipo == "1":
                    Personal.objects.create(
                        usuario=usuario,
                        codigo_profesor = datos.get("matricula", ""),
                        departamento = "no se obtiene del servicio",
                        tipo_contrato = "no se obtiene del servicio"
                    )

                #fecha de expiracion es igual a la fecha en la que se crea la credencial + 5 años
                fecha_creacion = timezone.now().date()
                fecha_expiracion = fecha_creacion + timedelta(days=5*365)
                
                
                Credencial.objects.create(usuario=usuario, fecha_expiracion=fecha_expiracion, estado=estado_credencial)
            
            return usuario
        
        return None