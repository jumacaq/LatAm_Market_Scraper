"""
Test de conexión a Supabase
Verifica que las credenciales funcionen correctamente
"""

from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=" * 60)
print("🧪 TEST DE CONEXIÓN A SUPABASE")
print("=" * 60)

# Obtener credenciales
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
service_key = os.getenv('SUPABASE_SERVICE_KEY')
# Verificar que existen
if not url or not key:
    print("❌ ERROR: Credenciales no encontradas en .env")
    print("\nVerifica que .env contenga:")
    print("  SUPABASE_URL=...")
    print("  SUPABASE_KEY=...")
    print("  SUPABASE_SERVICE_KEY=...")
    exit(1)

print(f"\n📍 URL: {url}")
print(f"🔑 Key: {key[:10]}..." )  # Solo mostrar inicio
print(f"🔑 Service Key: {service_key[:10]}..." )  # Solo mostrar inicio
try:
    # 1. Cliente para Operaciones de LECTURA (usa la clave 'anon' o 'key')
    print("\n🔌 Intentando conectar (Cliente Anónimo para SELECT)...")
    supabase_anon: Client = create_client(url, key)
    
    # 2. Cliente para Operaciones de ESCRITURA (usa la clave 'service_role')
    # Este cliente omite las políticas RLS y tiene control total.
    print("🔌 Creando cliente de servicio (para INSERT/DELETE)...")
    supabase_service: Client = create_client(url, service_key)
    print("✅ Clientes creados exitosamente!")
    
    # Test 1: Listar tablas
    print("\n✅ Conexión exitosa!")
    
    # Test 2: Query simple
    print("\n🔍 Probando query a tabla 'jobs'...")
    response = supabase_anon.table('jobs').select('*').limit(5).execute()
    
    print(f"✅ Query exitoso!")
    print(f"📊 Registros encontrados: {len(response.data)}")
    
    if len(response.data) > 0:
        print("\n📝 Primer registro:")
        first_job = response.data[0]
        print(f"   Título: {first_job.get('title', 'N/A')}")
        print(f"   Empresa: {first_job.get('company_name', 'N/A')}")
        print(f"   País: {first_job.get('country', 'N/A')}")
    else:
        print("\n💡 No hay registros aún (esto es normal en un proyecto nuevo)")
    
    # Test 3: Insertar dato de prueba
    print("\n🧪 Probando inserción de datos...")
    test_data = {
        'job_id': 'test-connection-001',
        'title': 'Test Connection Job',
        'company_name': 'Test Company',
        'country': 'Mexico',
        'source_platform': 'Test Script'
    }
    
    insert_response = supabase_service.table('jobs').insert(test_data).execute()
    print("✅ Inserción exitosa!")
    
    # Test 4: Limpiar dato de prueba
    print("🧹 Limpiando dato de prueba...")
    supabase_service.table('jobs').delete().eq('job_id', 'test-connection-001').execute()
    print("✅ Limpieza exitosa!")
    
    print("\n" + "=" * 60)
    print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 60)
    print("\n✅ Tu conexión a Supabase está funcionando correctamente!")
    print("✅ Puedes continuar con el siguiente paso")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\n🔧 Posibles soluciones:")
    print("  1. Verifica que SUPABASE_URL sea correcta")
    print("  2. Verifica que SUPABASE_KEY sea la 'anon public' key")
    print("  3. Verifica que las tablas estén creadas en Supabase")
    print("  4. Revisa que .env esté en la raíz del proyecto")
    exit(1)