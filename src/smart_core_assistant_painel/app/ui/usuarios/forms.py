from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError(
                _("Não encontramos uma conta ativa com este e-mail."),
                code="invalid_email",
            )
        return email

    def send_mail(
        self,
        subject_template_name: str,
        email_template_name: str,
        context: dict[str, object],
        from_email: str | None,
        to_email: str,
        html_email_template_name: str | None = None,
    ) -> None:
        """
        Envia email de recuperação de senha com fallback SSL em ambiente DEBUG.

        Este método sobrescreve o padrão do Django para adicionar um mecanismo
        de contingência que ignora a verificação de certificado SSL quando
        estamos em modo DEBUG e ocorre um erro de verificação SSL.
        Isso replica o comportamento do envio de convites de tenant.
        """
        import ssl

        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives, get_connection
        from django.template import loader

        subject = loader.render_to_string(subject_template_name, context)
        # Remove quebras de linha do assunto (Email RFC requer)
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(
            subject, body, from_email, [to_email]
        )
        if html_email_template_name:
            html_email = loader.render_to_string(
                html_email_template_name, context
            )
            email_message.attach_alternative(html_email, "text/html")

        try:
            email_message.send()
        except Exception as e:
            error_str = str(e)
            # Se for erro de certificado SSL e estivermos em DEBUG
            if "CERTIFICATE_VERIFY_FAILED" in error_str and settings.DEBUG:
                print(
                    f"Erro SSL detectado ({e}). "
                    "Tentando envio sem verificação SSL..."
                )
                # Criar contexto SSL não verificado
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                # Obter conexão com o contexto customizado
                connection = get_connection()
                connection.ssl_context = ctx
                email_message.connection = connection
                email_message.send()
            else:
                raise
