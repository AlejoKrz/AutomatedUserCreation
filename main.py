#!/usr/bin/env python3
"""
MAIN.PY - Punto de entrada principal del sistema
Usa configuración de logging desde config/settings.py
"""

import sys
import logging
import logging.config
from core.config import settings
from core.workflow_manager import WorkflowManager
from core.user_processor import UserProcessor
from core.progress_widget import ProgressWidget
from core.bots.bot_nomina import NominaApp
from core.bots.bot_ad import ADBot
from core.bots.bot_cobis import CobisApp
from core.bots.bot_syscard import SyscardsApp
from core.bots.bot_extreme import ExtremeWebApp
from core.credential_manager import CredentialManager

def setup_logging():
    """Configura el sistema de logging basado en settings.py"""
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'standard': {
                'format': settings.LOGGING['format'],
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': settings.LOGGING['level']
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': settings.LOGGING['file'],
                'maxBytes': settings.LOGGING['max_size'] * 1024 * 1024,  # Convertir MB a bytes
                'backupCount': settings.LOGGING['backup_count'],
                 'formatter': 'standard',
                'level': settings.LOGGING['level']
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': settings.LOGGING['level'],
                'propagate': True
            }
        }
    })

def main():
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Iniciando sistema de automatizacion")

    try:
        widget = ProgressWidget(None)  # Primero crea el widget

        # Inicializar el CredentialManager
        credential_manager = CredentialManager()

        # Cargar credenciales para cada bot
        bots = {
            "ad_bot": ADBot(widget=widget, log_dir="logs/ad"),
            "bot_nomina": NominaApp(
                app_path=settings.BOTS["NominaApp"]["app_path"],
                widget=widget,
                log_dir="logs/nomina",
                credentials=credential_manager.load_credentials("bot_nomina")
            ),
            "bot_cobis": CobisApp(
                app_path=settings.BOTS["Cobis"]["app_path"],
                widget=widget,
                log_dir="logs/cobis",
                credentials=credential_manager.load_credentials("bot_cobis")
            ),
            "bot_syscard": SyscardsApp(
                app_path=settings.BOTS["Syscard"]["app_path"],
                widget=widget,
                log_dir="logs/syscard",
                credentials=credential_manager.load_credentials("bot_syscard")
            ),
            "bot_extreme": ExtremeWebApp(
                widget=widget,
                log_dir="logs/extreme_web",
                credentials=credential_manager.load_credentials("bot_extreme")
            )
        }

        processor = UserProcessor(bots)
        workflow_manager = WorkflowManager(processor, widget)
        widget.workflow_manager = workflow_manager  # Asigna el workflow al widget
        widget.mainloop()

    except Exception as e:
        logger.critical(f"Error fatal: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Sistema detenido")

if __name__ == "__main__":
    main()