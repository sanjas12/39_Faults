import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from app.core.config import settings


class EmailService:
    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_email = settings.smtp_from
        self.enabled = settings.email_enabled

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Отправка email (синхронная)"""
        if not self.enabled:
            print(f"📧 Email отключён. Сообщение для {to_email}: {subject}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            # HTML версия
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            print(f"✅ Email отправлен на {to_email}")
            return True

        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            return False

    def send_fault_created(
        self, fault, project_name: str, user_name: str, recipients: List[str]
    ):
        """Уведомление о создании неисправности"""
        subject = f"🔴 Новая неисправность #{fault.id}: {fault.title}"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background: #dc3545; color: white; padding: 20px; border-radius: 8px; }}
                .content {{ padding: 20px; }}
                .field {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #555; }}
                .badge-critical {{ background: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; }}
                .badge-major {{ background: #ffc107; color: #333; padding: 4px 12px; border-radius: 12px; }}
                .badge-minor {{ background: #17a2b8; color: white; padding: 4px 12px; border-radius: 12px; }}
                .badge-trivial {{ background: #6c757d; color: white; padding: 4px 12px; border-radius: 12px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }}
                .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🆕 Новая неисправность</h2>
                <p>Создана пользователем <strong>{user_name}</strong></p>
            </div>
            <div class="content">
                <h3>#{fault.id} {fault.title}</h3>

                <div class="field">
                    <span class="label">Проект:</span> {project_name}
                </div>
                <div class="field">
                    <span class="label">Важность:</span>
                    <span class="badge-{fault.severity}">{fault.severity.upper()}</span>
                </div>
                <div class="field">
                    <span class="label">Статус:</span> {fault.status}
                </div>
                <div class="field">
                    <span class="label">Описание:</span><br>
                    {fault.description or "Нет описания"}
                </div>

                <div style="margin: 20px 0;">
                    <a href="http://localhost:3000/faults/{fault.id}" class="button">🔗 Перейти к неисправности</a>
                </div>
            </div>
            <div class="footer">
                <p>Это автоматическое уведомление от системы {settings.app_name}</p>
                <p>Не отвечайте на это письмо</p>
            </div>
        </body>
        </html>
        """

        for recipient in recipients:
            self._send_email(recipient, subject, html_content)

    def send_fault_updated(
        self, fault, user_name: str, changes: dict, recipients: List[str]
    ):
        """Уведомление об изменении неисправности"""
        subject = f"✏️ Изменена неисправность #{fault.id}: {fault.title}"

        changes_html = (
            "".join(
                [
                    f"<div class='field'><span class='label'>{field}:</span> "
                    f"<span style='color: #dc3545;'>{old}</span> → "
                    f"<span style='color: #28a745;'>{new}</span></div>"
                    for field, (old, new) in changes.items()
                ]
            )
            if changes
            else "<p>Изменения не указаны</p>"
        )

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background: #ffc107; color: #333; padding: 20px; border-radius: 8px; }}
                .content {{ padding: 20px; }}
                .field {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #555; }}
                .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; }}
                .badge-open {{ background: #dc3545; color: white; }}
                .badge-in_progress {{ background: #ffc107; color: #333; }}
                .badge-review {{ background: #17a2b8; color: white; }}
                .badge-closed {{ background: #28a745; color: white; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }}
                .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>✏️ Изменена неисправность</h2>
                <p>Изменения внесены пользователем <strong>{user_name}</strong></p>
            </div>
            <div class="content">
                <h3>#{fault.id} {fault.title}</h3>

                <div style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                    <h4>📝 Изменения:</h4>
                    {changes_html}
                </div>

                <div style="margin: 20px 0;">
                    <a href="http://localhost:3000/faults/{fault.id}" class="button">🔗 Перейти к неисправности</a>
                </div>
            </div>
            <div class="footer">
                <p>Это автоматическое уведомление от системы {settings.app_name}</p>
                <p>Не отвечайте на это письмо</p>
            </div>
        </body>
        </html>
        """

        for recipient in recipients:
            self._send_email(recipient, subject, html_content)

    def send_fault_status_changed(
        self, fault, new_status: str, user_name: str, recipients: List[str]
    ):
        """Уведомление об изменении статуса"""
        status_icons = {
            "open": "🟡 Открыта",
            "in_progress": "🟠 В работе",
            "review": "🔵 На проверке",
            "closed": "✅ Закрыта",
        }

        subject = f"🔄 Изменён статус неисправности #{fault.id}: {fault.title}"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background: #17a2b8; color: white; padding: 20px; border-radius: 8px; }}
                .content {{ padding: 20px; }}
                .status-open {{ background: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; }}
                .status-in_progress {{ background: #ffc107; color: #333; padding: 4px 12px; border-radius: 12px; }}
                .status-review {{ background: #17a2b8; color: white; padding: 4px 12px; border-radius: 12px; }}
                .status-closed {{ background: #28a745; color: white; padding: 4px 12px; border-radius: 12px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }}
                .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔄 Изменён статус неисправности</h2>
                <p>Пользователь <strong>{user_name}</strong> изменил статус</p>
            </div>
            <div class="content">
                <h3>#{fault.id} {fault.title}</h3>

                <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center; font-size: 18px;">
                    <span>Новый статус:</span>
                    <span class="status-{new_status}">{status_icons.get(new_status, new_status)}</span>
                </div>

                <div style="margin: 20px 0;">
                    <a href="http://localhost:3000/faults/{fault.id}" class="button">🔗 Перейти к неисправности</a>
                </div>
            </div>
            <div class="footer">
                <p>Это автоматическое уведомление от системы {settings.app_name}</p>
                <p>Не отвечайте на это письмо</p>
            </div>
        </body>
        </html>
        """

        for recipient in recipients:
            self._send_email(recipient, subject, html_content)


# Глобальный экземпляр
email_service = EmailService()
