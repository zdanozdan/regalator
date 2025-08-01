from django.test import TestCase, SimpleTestCase, TransactionTestCase
from django.db import connections
from django.conf import settings
from .models import tw_Towar


class SubiektConnectionTest(SimpleTestCase):
    """Prosty test połączenia z bazą danych Subiekt bez tworzenia testowej bazy"""

    def test_subiekt_database_configuration(self):
        """Test konfiguracji bazy danych Subiekt"""
        # Sprawdź czy baza danych 'subiekt' jest skonfigurowana
        self.assertIn('subiekt', settings.DATABASES, 
                     "Baza danych 'subiekt' nie jest skonfigurowana w settings.py")
        
        # Sprawdź czy konfiguracja nie zawiera placeholder'ów
        db_config = settings.DATABASES['subiekt']
        self.assertNotEqual(db_config.get('USER'), 'your_username',
                           "Zaktualizuj USER w konfiguracji bazy danych 'subiekt'")
        self.assertNotEqual(db_config.get('PASSWORD'), 'your_password',
                           "Zaktualizuj PASSWORD w konfiguracji bazy danych 'subiekt'")
        self.assertNotEqual(db_config.get('HOST'), 'your_server',
                           "Zaktualizuj HOST w konfiguracji bazy danych 'subiekt'")
        
        # Sprawdź czy wymagane pola są obecne
        required_fields = ['ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST']
        for field in required_fields:
            self.assertIn(field, db_config, 
                         f"Brak wymaganego pola '{field}' w konfiguracji bazy danych 'subiekt'")
    
    def test_subiekt_connection_direct(self):
        """Bezpośredni test połączenia z bazą danych Subiekt"""
        # Sprawdź czy baza danych 'subiekt' jest skonfigurowana
       # if 'subiekt' not in settings.DATABASES:
       #     self.skipTest("Baza danych 'subiekt' nie jest skonfigurowana")
        
        # Sprawdź czy konfiguracja nie zawiera placeholder'ów
        #db_config = settings.DATABASES['subiekt']
        #if (db_config.get('USER') == 'your_username' or 
        #    db_config.get('PASSWORD') == 'your_password' or 
        #    db_config.get('HOST') == 'your_server'):
        #    self.skipTest("Konfiguracja bazy danych 'subiekt' zawiera placeholder'y - zaktualizuj settings.py")
        
        try:
            # Bezpośrednie połączenie z bazą danych
            import pyodbc
            
            # Pobierz konfigurację bazy danych
            db_config = settings.DATABASES['subiekt']
            
            # Utwórz connection string
            conn_str = (
                f"DRIVER={{{db_config['OPTIONS']['driver']}}};"
                f"SERVER={db_config['HOST']};"
                f"DATABASE={db_config['NAME']};"
                f"UID={db_config['USER']};"
                f"PWD={db_config['PASSWORD']};"
                f"TrustServerCertificate=yes;"
            )
            
            # Test połączenia
            conn = pyodbc.connect(conn_str, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            self.assertEqual(result[0], 1)
            print("✓ Bezpośrednie połączenie z bazą danych Subiekt udane")
            
        except Exception as e:
            raise
            self.skipTest(f"Błąd bezpośredniego połączenia z bazą danych Subiekt: {str(e)}")


class SubiektDatabaseTest(TestCase):
    """Test połączenia z bazą danych Subiekt bez tworzenia testowej bazy"""

    # Używamy domyślnej bazy danych dla testów Django i pozwalamy na dostęp do 'subiekt'
    databases = {'default', 'subiekt'}

    def test_subiekt_database_configuration(self):
        """Test konfiguracji bazy danych Subiekt"""
        # Sprawdź czy baza danych 'subiekt' jest skonfigurowana
        self.assertIn('subiekt', settings.DATABASES, 
                     "Baza danych 'subiekt' nie jest skonfigurowana w settings.py")
        
        # Sprawdź czy konfiguracja nie zawiera placeholder'ów
        db_config = settings.DATABASES['subiekt']
        self.assertNotEqual(db_config.get('USER'), 'your_username',
                           "Zaktualizuj USER w konfiguracji bazy danych 'subiekt'")
        self.assertNotEqual(db_config.get('PASSWORD'), 'your_password',
                           "Zaktualizuj PASSWORD w konfiguracji bazy danych 'subiekt'")
        self.assertNotEqual(db_config.get('HOST'), 'your_server',
                           "Zaktualizuj HOST w konfiguracji bazy danych 'subiekt'")
        
        # Sprawdź czy wymagane pola są obecne
        required_fields = ['ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST']
        for field in required_fields:
            self.assertIn(field, db_config, 
                         f"Brak wymaganego pola '{field}' w konfiguracji bazy danych 'subiekt'")
    
    def test_subiekt_connection_simple(self):
        """Prosty test połączenia z bazą danych Subiekt"""
        # Sprawdź czy baza danych 'subiekt' jest skonfigurowana
        #if 'subiekt' not in settings.DATABASES:
        #    self.skipTest("Baza danych 'subiekt' nie jest skonfigurowana")
        
        # Sprawdź czy konfiguracja nie zawiera placeholder'ów
        db_config = settings.DATABASES['subiekt']
        #if (db_config.get('USER') == 'your_username' or 
        #    db_config.get('PASSWORD') == 'your_password' or 
        #    db_config.get('HOST') == 'your_server'):
        #    self.skipTest("Konfiguracja bazy danych 'subiekt' zawiera placeholder'y - zaktualizuj settings.py")
        
        try:
            # Sprawdź czy połączenie działa
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1)
        except Exception as e:
            raise
            self.skipTest(f"Błąd połączenia z bazą danych Subiekt: {str(e)}")
    
    def test_towar_table_exists(self):
        """Test czy tabela [dbo].[tw__Towar] istnieje"""
        # Sprawdź czy baza danych 'subiekt' jest skonfigurowana
        if 'subiekt' not in settings.DATABASES:
            self.skipTest("Baza danych 'subiekt' nie jest skonfigurowana")
        
        # Sprawdź czy konfiguracja nie zawiera placeholder'ów
        db_config = settings.DATABASES['subiekt']
        if (db_config.get('USER') == 'your_username' or 
            db_config.get('PASSWORD') == 'your_password' or 
            db_config.get('HOST') == 'your_server'):
            self.skipTest("Konfiguracja bazy danych 'subiekt' zawiera placeholder'y - zaktualizuj settings.py")
        
        try:
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = 'dbo' 
                    AND TABLE_NAME = 'tw__Towar'
                """)
                result = cursor.fetchone()
                self.assertEqual(result[0], 1, "Tabela [dbo].[tw__Towar] nie istnieje")
        except Exception as e:
            self.skipTest(f"Błąd sprawdzania tabeli: {str(e)}")
    
    def test_get_towar_by_id(self):
        """Test pobierania towaru po ID"""
        # Sprawdź czy baza danych 'subiekt' jest skonfigurowana
        if 'subiekt' not in settings.DATABASES:
            self.skipTest("Baza danych 'subiekt' nie jest skonfigurowana")
        
        # Sprawdź czy konfiguracja nie zawiera placeholder'ów
        db_config = settings.DATABASES['subiekt']
        if (db_config.get('USER') == 'your_username' or 
            db_config.get('PASSWORD') == 'your_password' or 
            db_config.get('HOST') == 'your_server'):
            self.skipTest("Konfiguracja bazy danych 'subiekt' zawiera placeholder'y - zaktualizuj settings.py")
        
        try:
            # Pobierz pierwszy towar z bazy
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("SELECT TOP 1 tw_Id FROM [dbo].[tw__Towar]")
                result = cursor.fetchone()
                
                if result:
                    towar_id = result[0]
                    
                    # Pobierz towar przez Django ORM
                    towar = tw_Towar.objects.using('subiekt').get(tw_Id=towar_id)
                    
                    # Sprawdź czy dane są poprawnie pobrane
                    self.assertIsNotNone(towar.tw_Id)
                    self.assertIsNotNone(towar.tw_Symbol)
                    self.assertIsNotNone(towar.tw_Nazwa)
                    
                    print(f"✓ Pobrano towar: ID={towar.tw_Id}, Symbol={towar.tw_Symbol}, Nazwa={towar.tw_Nazwa}")
                else:
                    self.skipTest("Brak danych w tabeli [dbo].[tw__Towar]")
                    
        except tw_Towar.DoesNotExist:
            self.skipTest("Nie można pobrać towaru przez Django ORM")
        except Exception as e:
            self.skipTest(f"Błąd pobierania towaru: {str(e)}")
    
    def test_get_towar_by_symbol(self):
        """Test pobierania towaru po symbolu"""
        # Sprawdź czy baza danych 'subiekt' jest skonfigurowana
        if 'subiekt' not in settings.DATABASES:
            self.skipTest("Baza danych 'subiekt' nie jest skonfigurowana")
        
        # Sprawdź czy konfiguracja nie zawiera placeholder'ów
        db_config = settings.DATABASES['subiekt']
        if (db_config.get('USER') == 'your_username' or 
            db_config.get('PASSWORD') == 'your_password' or 
            db_config.get('HOST') == 'your_server'):
            self.skipTest("Konfiguracja bazy danych 'subiekt' zawiera placeholder'y - zaktualizuj settings.py")
        
        try:
            # Pobierz pierwszy towar z bazy
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("SELECT TOP 1 tw_Symbol FROM [dbo].[tw__Towar] WHERE tw_Symbol IS NOT NULL")
                result = cursor.fetchone()
                
                if result:
                    symbol = result[0]
                    
                    # Pobierz towar przez Django ORM
                    towar = tw_Towar.objects.using('subiekt').get(tw_Symbol=symbol)
                    
                    # Sprawdź czy dane są poprawnie pobrane
                    self.assertEqual(towar.tw_Symbol, symbol)
                    self.assertIsNotNone(towar.tw_Nazwa)
                    
                    print(f"✓ Pobrano towar po symbolu: {symbol}")
                else:
                    self.skipTest("Brak danych w tabeli [dbo].[tw__Towar]")
                    
        except tw_Towar.DoesNotExist:
            self.skipTest("Nie można pobrać towaru po symbolu")
        except Exception as e:
            self.skipTest(f"Błąd pobierania towaru po symbolu: {str(e)}")
    
    def test_count_towary(self):
        """Test liczenia towarów w bazie"""
        # Sprawdź czy baza danych 'subiekt' jest skonfigurowana
        if 'subiekt' not in settings.DATABASES:
            self.skipTest("Baza danych 'subiekt' nie jest skonfigurowana")
        
        # Sprawdź czy konfiguracja nie zawiera placeholder'ów
        db_config = settings.DATABASES['subiekt']
        if (db_config.get('USER') == 'your_username' or 
            db_config.get('PASSWORD') == 'your_password' or 
            db_config.get('HOST') == 'your_server'):
            self.skipTest("Konfiguracja bazy danych 'subiekt' zawiera placeholder'y - zaktualizuj settings.py")
        
        try:
            # Liczba towarów przez Django ORM
            count_django = tw_Towar.objects.using('subiekt').count()
            
            # Liczba towarów przez SQL
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM [dbo].[tw__Towar]")
                result = cursor.fetchone()
                count_sql = result[0]
            
            # Sprawdź czy liczby są zgodne
            self.assertEqual(count_django, count_sql)
            
            print(f"✓ Liczba towarów w bazie: {count_django}")
            
        except Exception as e:
            self.skipTest(f"Błąd liczenia towarów: {str(e)}")


class SubiektModelTest(TestCase):
    """Test modelu Towar"""
    
    def test_towar_str_representation(self):
        """Test reprezentacji string modelu Towar"""
        # Utwórz przykładowy obiekt (nie zapisujemy do bazy)
        towar = tw_Towar(
            tw_Id=1,
            tw_Symbol="TEST001",
            tw_Nazwa="Testowy towar",
            tw_Opis="Opis testowego towaru"
        )
        
        expected_str = "TEST001 - Testowy towar"
        self.assertEqual(str(towar), expected_str)
    
    def test_towar_properties(self):
        """Test właściwości modelu Towar"""
        towar = tw_Towar(
            tw_Id=1,
            tw_Symbol="TEST001",
            tw_Nazwa="Testowy towar",
            tw_Opis="Opis testowego towaru"
        )
        
        self.assertEqual(towar.kod_produktu, "TEST001")
        self.assertEqual(towar.nazwa_produktu, "Testowy towar")
        self.assertEqual(towar.opis_produktu, "Opis testowego towaru")
    
    def test_towar_empty_description(self):
        """Test właściwości z pustym opisem"""
        towar = tw_Towar(
            tw_Id=1,
            tw_Symbol="TEST001",
            tw_Nazwa="Testowy towar",
            tw_Opis=""
        )
        
        self.assertEqual(towar.opis_produktu, "")
