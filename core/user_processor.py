from .config import settings
from .models import ProcessResult

# Mapeo entre el bot y el campo que indica su rol
BOT_ROLE_FIELD_MAP = {
    "bot_nomina": "Cargo_x003a__x0020_Cargo_x0020_e0",
    "ad_bot": "Cargo",
    "bot_cobis": "Cargo_x003a__x0020_Rol_x0020_en_",
    "bot_syscard": "Cargo_x003a__x0020_Rol_x0020_Sys",
    "bot_extreme": "Cargo_x003a__x0020_Rol_x0020_Ext",
}

# Bots que deben ejecutarse siempre, sin importar el valor del campo
MANDATORY_BOTS = {"ad_bot", "bot_nomina"}

class UserProcessor:
    def __init__(self, bots):
        self.bots = bots
        self.bot_order = (
            settings.BOTS_A_PROBAR
            if getattr(settings, "TEST_MODE", False)
            else ["bot_nomina", "ad_bot", "bot_cobis", "bot_syscard", "bot_extreme"]
        )

    def process_user(self, user, pause_event=None):
        results = []

        for bot_name in self.bot_order:
            # Verificar si el bot no es obligatorio
            if bot_name not in MANDATORY_BOTS:
                role_field = BOT_ROLE_FIELD_MAP.get(bot_name)
                if not role_field:
                    continue  # Sin campo asignado → no se ejecuta

                user_role_value = getattr(user, role_field, "N/A").strip()
                if user_role_value.upper() == "N/A":
                    continue  # El usuario no tiene rol en ese bot → omitir

            bot = self.bots.get(bot_name)
            if not bot:
                continue  # Bot no disponible → omitir

            if pause_event:
                pause_event.wait()

            try:
                result = bot.execute(user)
                results.append(ProcessResult(
                    bot_name=bot_name,
                    success=True,
                    message=f"{bot_name}: {result}"
                ))
            except Exception as e:
                results.append(ProcessResult(
                    bot_name=bot_name,
                    success=False,
                    message=f"Error en {bot_name}: {str(e)}"
                ))
                break

        return results
