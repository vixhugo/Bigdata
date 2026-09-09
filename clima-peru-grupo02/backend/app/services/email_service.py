"""
Servicio de notificaciones por correo electrónico.
Usa SMTP para enviar emails.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
import smtplib
from html import escape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from contextlib import contextmanager

from app.config import settings


class EmailService:
    """Servicio de envío de emails."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        self.frontend_url = settings.FRONTEND_URL
        self.is_development = settings.APP_ENV.lower() in {"development", "dev", "local"}
        
        self.is_configured = bool(
            self.smtp_host and self.smtp_user and self.smtp_password
        )
    
    @contextmanager
    def _get_connection(self):
        """Obtiene una conexión SMTP segura."""
        if not self.is_configured:
            raise ValueError(
                "Configuración SMTP incompleta. Verifica SMTP_HOST, SMTP_USER, SMTP_PASSWORD."
            )
        
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        try:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            yield server
        finally:
            server.quit()
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Envía un email.
        Retorna True si el envío fue exitoso, False en caso contrario.
        """
        if not self.is_configured:
            if self.is_development:
                print(f"[EMAIL SIMULADO] A {to_email}: {subject}")
                print(html_content[:200] + "...")
                return True
            print("Error: SMTP no está configurado en producción.")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = to_email
            
            # Contenido de texto plano
            if text_content:
                part_text = MIMEText(text_content, "plain")
                msg.attach(part_text)
            
            # Contenido HTML
            part_html = MIMEText(html_content, "html")
            msg.attach(part_html)
            
            with self._get_connection() as server:
                server.sendmail(self.smtp_from, to_email, msg.as_string())
            
            return True
        
        except Exception as e:
            print(f"Error al enviar email a {to_email}: {e}")
            return False
    
    def send_invitation_email(
        self,
        invitation_id: int,
        email: str,
        token: str,
        full_name: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """
        Envía una invitación por email.
        """
        if not self.is_configured:
            print(f"[EMAIL SIMULADO] Enviar invitación a {email}")
            print(f"Token: {token}")
            return True
        
        full_name = full_name or "Usuario"
        safe_name = escape(full_name)
        accept_url = f"{self.frontend_url}/accept-invitation?token={token}"
        expiration_text = (
            expires_at.strftime('%d/%m/%Y a las %H:%M')
            if expires_at else 'la fecha indicada en el sistema'
        )
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: linear-gradient(135deg, #0ea5e9, #6366f1); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">MeteoPerú</h1>
                <p style="color: #e0f2fe; margin: 5px 0 0;">Sistema Meteorológico del Perú</p>
            </div>
            
            <div style="background-color: white; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #1e293b;">¡Invitación para unirte a MeteoPerú!</h2>
                
                <p style="color: #475569; line-height: 1.6;">
                    Hola <strong>{safe_name}</strong>,
                </p>
                
                <p style="color: #475569; line-height: 1.6;">
                    Te han invitado a unirte a nuestra plataforma meteorológica. 
                    Con MeteoPerú podrás:
                </p>
                
                <ul style="color: #475569; line-height: 2;">
                    <li>Consultar el pronóstico del tiempo para todo el Perú</li>
                    <li>Explorar datos históricos climáticos</li>
                    <li>Visualizar mapas interactivos</li>
                    <li>Comparar climas entre diferentes ciudades</li>
                    <li>Recibir alertas meteorológicas</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{accept_url}" 
                       style="display: inline-block; background: linear-gradient(135deg, #0ea5e9, #6366f1); 
                              color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 8px; font-weight: bold; font-size: 16px;">
                        Aceptar Invitación
                    </a>
                </div>
                
                <p style="color: #64748b; font-size: 14px;">
                    Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                    <a href="{accept_url}">{accept_url}</a>
                </p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="color: #94a3b8; font-size: 12px;">
                    Esta invitación expirará el {expiration_text}.<br>
                    Si no esperabas esta invitación, por favor ignora este correo.
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;">
                <p>© 2026 MeteoPerú - Sistema Meteorológico del Perú</p>
                <p>Hecho con ❤️ para el Perú</p>
            </div>
        </div>
        """
        
        text_content = f"""
        ¡Invitación para unirte a MeteoPerú!
        
        Hola {full_name},
        
        Te han invitado a unirte a nuestra plataforma meteorológica.
        
        Con MeteoPerú podrás:
        - Consultar el pronóstico del tiempo para todo el Perú
        - Explorar datos históricos climáticos
        - Visualizar mapas interactivos
        - Comparar climas entre diferentes ciudades
        - Recibir alertas meteorológicas
        
        Acepta tu invitación aquí: {accept_url}
        
        Esta invitación expirará el {expiration_text}.
        Si no esperabas esta invitación, por favor ignora este correo.
        
        © 2026 MeteoPerú - Sistema Meteorológico del Perú
        """
        
        return self.send_email(
            to_email=email,
            subject=f"Invitación para unirte a MeteoPerú",
            html_content=html_content,
            text_content=text_content,
        )
    
    def send_admin_notification(self, admin_email: str, user_name: str, user_email: str) -> bool:
        """
        Notifica al admin que alguien aceptó una invitación.
        """
        if not self.is_configured:
            print(f"[EMAIL SIMULADO] Notificar a {admin_email}: {user_name} aceptó invitación")
            return True
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: linear-gradient(135deg, #0ea5e9, #6366f1); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Nueva Aceptación de Invitación</h1>
            </div>
            
            <div style="background-color: white; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="color: #475569; line-height: 1.6;">
                    El siguiente usuario ha aceptado tu invitación:
                </p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Nombre:</strong> {user_name}</p>
                    <p style="margin: 5px 0;"><strong>Email:</strong> {user_email}</p>
                    <p style="margin: 5px 0;"><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <p style="color: #475569; line-height: 1.6;">
                    Puedes gestionar este usuario desde el panel de administración.
                </p>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{self.frontend_url}/admin" 
                       style="display: inline-block; background: linear-gradient(135deg, #0ea5e9, #6366f1); 
                              color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 8px; font-weight: bold;">
                        Ir al Panel de Administración
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;">
                <p>© 2026 MeteoPerú - Sistema Meteorológico del Perú</p>
            </div>
        </div>
        """
        
        return self.send_email(
            to_email=admin_email,
            subject=f"Nuevo usuario aceptó tu invitación: {user_name}",
            html_content=html_content,
        )
    
    def send_registration_notification(self, admin_email: str, user_name: str, user_email: str) -> bool:
        """
        Notifica al admin que alguien se registró (si el registro no requiere invitación).
        """
        if not self.is_configured:
            print(f"[EMAIL SIMULADO] Notificar a {admin_email}: {user_name} se registró")
            return True
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Nuevo Registro de Usuario</h1>
            </div>
            
            <div style="background-color: white; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="color: #475569; line-height: 1.6;">
                    Se ha registrado un nuevo usuario en MeteoPerú:
                </p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Nombre:</strong> {user_name}</p>
                    <p style="margin: 5px 0;"><strong>Email:</strong> {user_email}</p>
                    <p style="margin: 5px 0;"><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p style="margin: 5px 0;"><strong>Método:</strong> Registro directo</p>
                </div>
                
                <p style="color: #475569; line-height: 1.6;">
                    Este usuario tiene el rol "Usuario" por defecto. Puedes modificarlo desde el panel de administración.
                </p>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{self.frontend_url}/admin/members" 
                       style="display: inline-block; background: linear-gradient(135deg, #10b981, #059669); 
                              color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 8px; font-weight: bold;">
                        Gestionar Usuario
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;">
                <p>© 2026 MeteoPerú - Sistema Meteorológico del Perú</p>
            </div>
        </div>
        """
        
        return self.send_email(
            to_email=admin_email,
            subject=f"Nuevo registro en MeteoPerú: {user_name}",
            html_content=html_content,
        )
