# fix_all_safe.py - VERSIÓN EXTRA SEGURA
import os
import django
import subprocess
import sys
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction, connection

# Configurar entorno Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budsi_django.settings")
django.setup()

User = get_user_model()

def verify_and_confirm():
    """Verificación extra de seguridad con confirmación del usuario"""
    print("🔐 VERIFICACIÓN DE SEGURIDAD")
    print("=" * 50)
    
    # Mostrar superusuarios
    superusers = User.objects.filter(is_superuser=True)
    print("👑 SUPERUSUARIOS QUE SERÁN PRESERVADOS:")
    for user in superusers:
        print(f"   • {user.email} (desde: {user.date_joined.date()})")
    
    if not superusers.exists():
        print("⚠️  ¡ADVERTENCIA! No hay superusuarios en el sistema")
    
    # Mostrar estadísticas de datos a eliminar
    print("\n📊 DATOS QUE SERÁN ELIMINADOS:")
    models_to_clean = ['Invoice', 'Contact', 'FiscalProfile', 'Project']
    for model_name in models_to_clean:
        try:
            model = apps.get_model('budsi_database', model_name)
            count = model.objects.count()
            print(f"   • {model_name}: {count} registros")
        except:
            print(f"   • {model_name}: No disponible")
    
    # Confirmación del usuario
    print("\n" + "=" * 50)
    confirm = input("¿ESTÁS SEGURO de que quieres continuar? (escribe 'SI' para confirmar): ")
    
    if confirm != 'SI':
        print("❌ Operación cancelada por el usuario")
        sys.exit(0)
    
    return list(superusers)

@transaction.atomic
def purge_all_except_superusers(superusers):
    """Limpiar base de datos preservando superusuarios - VERSIÓN SEGURA"""
    print("\n⚠️  INICIANDO LIMPIEZA DE BASE DE DATOS")
    print("--------------------------------------------------")
    
    super_emails = [u.email for u in superusers]
    print(f"✅ Superusuarios protegidos: {super_emails}\n")
    
    # ORDEN CRÍTICO DE ELIMINACIÓN
    deletion_order = [
        'InvoiceLine', 'Invoice', 'TaxPeriod', 
        'FiscalConfig', 'Project', 'Contact', 'FiscalProfile'
    ]
    
    deleted_total = 0
    for model_name in deletion_order:
        try:
            model = apps.get_model('budsi_database', model_name)
            count = model.objects.count()
            if count > 0:
                print(f"🗑️  Eliminando {count} registros de {model_name}...")
                model.objects.all().delete()
                deleted_total += count
        except Exception as e:
            print(f"⚠️  Error con {model_name}: {e}")
    
    # SOLO eliminar usuarios normales
    normal_users = User.objects.filter(is_superuser=False)
    user_count = normal_users.count()
    if user_count:
        print(f"🧍 Eliminando {user_count} usuario(s) normales...")
        # MOSTRAR qué usuarios se eliminarán
        for user in normal_users:
            print(f"   • {user.email} (normal user)")
        normal_users.delete()
        deleted_total += user_count
    
    print(f"\n🎉 LIMPIEZA COMPLETA: {deleted_total} registros eliminados")
    print(f"   👑 Superusuarios preservados: {len(superusers)}")
    print("--------------------------------------------------")

# ... (el resto del código igual que antes)

def main():
    """Función principal - VERSIÓN SEGURA"""
    print("🚀 INICIANDO REPARACIÓN COMPLETA DEL SISTEMA")
    print("=" * 60)
    
    # VERIFICACIÓN EXTRA DE SEGURIDAD
    superusers = verify_and_confirm()
    
    # Proceder con la limpieza (usando los superusuarios verificados)
    try:
        purge_all_except_superusers(superusers)
        print("✅ Base de datos limpiada exitosamente")
    except Exception as e:
        print(f"❌ Error limpiando base de datos: {e}")
    
    # ... resto del proceso de reparación de migraciones

if __name__ == "__main__":
    main()