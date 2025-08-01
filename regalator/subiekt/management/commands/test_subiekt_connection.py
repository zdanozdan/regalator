from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings
from subiekt.models import tw_Towar, tw_Stan, dok_Dokument


class Command(BaseCommand):
    help = 'Test połączenia z bazą danych Subiekt i pobierania towarów'

    def add_arguments(self, parser):
        parser.add_argument(
            '--towar-id',
            type=int,
            help='ID towaru do pobrania'
        )
        parser.add_argument(
            '--symbol',
            type=str,
            help='Symbol towaru do wyszukania'
        )
        parser.add_argument(
            '--mag-id',
            type=int,
            default=2,
            help='ID magazynu (domyślnie 2)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Uruchom wszystkie testy'
        )

    def display_menu(self):
        """Display the interactive menu"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('MENU TESTOWANIA SUBIEKT'))
        self.stdout.write('='*50)
        self.stdout.write('1. Test połączenia z bazą danych')
        self.stdout.write('2. Test tabeli tw__Towar')
        self.stdout.write('3. Test tabeli tw_Stan')
        self.stdout.write('4. Test pobierania towaru po ID')
        self.stdout.write('5. Test pobierania towaru po symbolu')
        self.stdout.write('6. Test get_products_with_stock')
        self.stdout.write('7. Test get_product_by_id')
        self.stdout.write('8. Test dok_Dokument i get_zk')
        self.stdout.write('9. Test dok_Dokument i get_zd')
        self.stdout.write('10. Test get_zk_pozycje')
        self.stdout.write('11. Test get_zd_pozycje')
        self.stdout.write('0. Wyjście')
        self.stdout.write('='*50)

    def get_user_choice(self):
        """Get user choice from menu"""
        while True:
            try:
                choice = input('\nWybierz test (0-11): ').strip()
                if choice == '0':
                    return None
                choice_num = int(choice)
                if 1 <= choice_num <= 11:
                    return choice_num
                else:
                    self.stdout.write(self.style.ERROR('Nieprawidłowy wybór. Wprowadź liczbę 0-11.'))
            except ValueError:
                self.stdout.write(self.style.ERROR('Nieprawidłowy format. Wprowadź liczbę 0-11.'))

    def test_database_connection(self):
        """Test 1: Połączenie z bazą danych"""
        self.stdout.write('\n--- Test 1: Połączenie z bazą danych ---')
        try:
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.stdout.write(
                    self.style.SUCCESS('✓ Połączenie z bazą danych udane')
                )
                return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd połączenia z bazą danych: {str(e)}')
            )
            return False

    def test_towar_table(self):
        """Test 2: Sprawdzenie tabeli tw__Towar"""
        self.stdout.write('\n--- Test 2: Tabela tw__Towar ---')
        try:
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = 'dbo' 
                    AND TABLE_NAME = 'tw__Towar'
                """)
                result = cursor.fetchone()
                if result[0] > 0:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Tabela [dbo].[tw__Towar] istnieje')
                    )
                    
                    cursor.execute("SELECT COUNT(*) FROM [dbo].[tw__Towar]")
                    towar_count = cursor.fetchone()[0]
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Liczba towarów w tabeli: {towar_count}')
                    )
                    return True
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ Tabela [dbo].[tw__Towar] nie istnieje')
                    )
                    return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd sprawdzania tabeli: {str(e)}')
            )
            return False

    def test_stan_table(self):
        """Test 3: Sprawdzenie tabeli tw_Stan"""
        self.stdout.write('\n--- Test 3: Tabela tw_Stan ---')
        try:
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = 'dbo' 
                    AND TABLE_NAME = 'tw_Stan'
                """)
                result = cursor.fetchone()
                if result[0] > 0:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Tabela [dbo].[tw_Stan] istnieje')
                    )
                    
                    cursor.execute("SELECT COUNT(*) FROM [dbo].[tw_Stan]")
                    stan_count = cursor.fetchone()[0]
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Liczba stanów w tabeli: {stan_count}')
                    )
                    return True
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ Tabela [dbo].[tw_Stan] nie istnieje')
                    )
                    return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd sprawdzania tabeli stanów: {str(e)}')
            )
            return False

    def test_get_product_by_id(self, towar_id=None):
        """Test 4: Pobieranie towaru po ID"""
        self.stdout.write('\n--- Test 4: get_product_by_id ---')
        
        if not towar_id:
            # Get first product ID from database
            try:
                with connections['subiekt'].cursor() as cursor:
                    cursor.execute("SELECT TOP 1 tw_Id FROM [dbo].[tw__Towar] ORDER BY tw_Id")
                    first_product_id = cursor.fetchone()
                    if first_product_id:
                        towar_id = first_product_id[0]
                    else:
                        self.stdout.write(
                            self.style.WARNING('⚠ Brak towarów w bazie do testowania')
                        )
                        return False
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Błąd pobierania ID towaru: {str(e)}')
                )
                return False

        try:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Testuję get_product_by_id z ID={towar_id}:')
            )
            
            product = tw_Towar.subiekt_objects.get_product_by_id(towar_id)
            if product:
                self.stdout.write(f"  Znaleziono: {product.tw_Symbol} - {product.tw_Nazwa}")
                self.stdout.write(f"  Stan: {product.st_Stan}, Zarezerwowany: {product.st_StanRez}")
                if product.tw_Opis:
                    self.stdout.write(f"  Opis: {product.tw_Opis}")
                if hasattr(product, 'grt_Nazwa') and product.grt_Nazwa:
                    self.stdout.write(f"  Grupa: {product.grt_Nazwa}")
                else:
                    self.stdout.write(f"  Grupa: Brak grupy")
                return True
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Nie znaleziono towaru o ID={towar_id}')
                )
                return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd pobierania towaru ID={towar_id}: {str(e)}')
            )
            return False

    def test_get_product_by_symbol(self, symbol=None):
        """Test 5: Pobieranie towaru po symbolu"""
        self.stdout.write('\n--- Test 5: get_product_by_symbol ---')
        
        if not symbol:
            # Get first product symbol from database
            try:
                with connections['subiekt'].cursor() as cursor:
                    cursor.execute("SELECT TOP 1 tw_Symbol FROM [dbo].[tw__Towar] WHERE tw_Symbol IS NOT NULL ORDER BY tw_Id")
                    first_symbol = cursor.fetchone()
                    if first_symbol:
                        symbol = first_symbol[0]
                    else:
                        self.stdout.write(
                            self.style.WARNING('⚠ Brak symboli towarów w bazie do testowania')
                        )
                        return False
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Błąd pobierania symbolu towaru: {str(e)}')
                )
                return False

        try:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Testuję get_product_by_symbol z Symbol={symbol}:')
            )
            
            product = tw_Towar.subiekt_objects.get_product_by_id(symbol)
            if product:
                self.stdout.write(f"  Znaleziono: {product.tw_Symbol} - {product.tw_Nazwa}")
                self.stdout.write(f"  Stan: {product.st_Stan}, Zarezerwowany: {product.st_StanRez}")
                if product.tw_Opis:
                    self.stdout.write(f"  Opis: {product.tw_Opis}")
                if hasattr(product, 'grt_Nazwa') and product.grt_Nazwa:
                    self.stdout.write(f"  Grupa: {product.grt_Nazwa}")
                else:
                    self.stdout.write(f"  Grupa: Brak grupy")
                return True
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Nie znaleziono towaru o Symbol={symbol}')
                )
                return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd pobierania towaru Symbol={symbol}: {str(e)}')
            )
            return False

    def test_get_products_with_stock(self):
        """Test 6: get_products_with_stock"""
        self.stdout.write('\n--- Test 6: get_products_with_stock ---')
        try:
            mag_id = getattr(settings, 'SUBIEKT_MAGAZYN_ID', 2)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Używam nowej metody z managera subiekt_objects.get_products_with_stock (magazyn {mag_id}):')
            )
            towary = tw_Towar.subiekt_objects.get_products_with_stock(limit=5)
            for towar in towary:
                group_info = f" (Grupa: {towar.grt_Nazwa})" if hasattr(towar, 'grt_Nazwa') and towar.grt_Nazwa else " (Grupa: Brak)"
                self.stdout.write(f"  {towar.tw_Id}: {towar.tw_Symbol} - {towar.tw_Nazwa} (Stan: {towar.st_Stan}, Zarezerwowany: {towar.st_StanRez}){group_info}")
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd pobierania towarów: {str(e)}')
            )
            return False

    def test_get_product_by_id_manager(self):
        """Test 7: get_product_by_id manager method"""
        self.stdout.write('\n--- Test 7: get_product_by_id manager ---')
        try:
            # Test with existing product ID
            with connections['subiekt'].cursor() as cursor:
                cursor.execute("SELECT TOP 1 tw_Id FROM [dbo].[tw__Towar] ORDER BY tw_Id")
                first_product_id = cursor.fetchone()
                
                if first_product_id:
                    test_id = first_product_id[0]
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Testuję get_product_by_id z ID={test_id}:')
                    )
                    
                    product = tw_Towar.subiekt_objects.get_product_by_id(test_id)
                    if product:
                        self.stdout.write(f"  Znaleziono: {product.tw_Symbol} - {product.tw_Nazwa}")
                        self.stdout.write(f"  Stan: {product.st_Stan}, Zarezerwowany: {product.st_StanRez}")
                        if product.tw_Opis:
                            self.stdout.write(f"  Opis: {product.tw_Opis}")
                        if hasattr(product, 'grt_Nazwa') and product.grt_Nazwa:
                            self.stdout.write(f"  Grupa: {product.grt_Nazwa}")
                        else:
                            self.stdout.write(f"  Grupa: Brak grupy")
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Nie znaleziono towaru o ID={test_id}')
                        )
                        return False
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠ Brak towarów w bazie do testowania')
                    )
                    return False
                    
                # Test with non-existent ID
                self.stdout.write(
                    self.style.SUCCESS('✓ Testuję get_product_by_id z nieistniejącym ID=999999:')
                )
                non_existent_product = tw_Towar.subiekt_objects.get_product_by_id(999999)
                if non_existent_product is None:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Poprawnie zwrócono None dla nieistniejącego towaru')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ Błąd: Zwrócono produkt dla nieistniejącego ID')
                    )
                    return False
                    
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd testowania get_product_by_id: {str(e)}')
            )
            return False

    def test_dok_dokument_get_zk(self):
        """Test 8: dok_Dokument i get_zk"""
        self.stdout.write('\n--- Test 8: dok_Dokument i get_zk ---')
        try:
            self.stdout.write(
                self.style.SUCCESS('✓ Testuję metodę get_zk():')
            )
            zk_documents = dok_Dokument.dokument_objects.get_zk(limit=10)
            
            if zk_documents:
                self.stdout.write(f"  ✓ Pobrano {len(zk_documents)} dokumentów ZK:")
                for i, doc in enumerate(zk_documents, 1):
                    self.stdout.write(f"    {i}. {doc.dok_NrPelny} - {doc.document_type_name}")
                    self.stdout.write(f"       Magazyn: {doc.dok_MagId}")
                    if hasattr(doc, 'dok_DataWyst') and doc.dok_DataWyst:
                        self.stdout.write(f"       Data wystawienia: {doc.dok_DataWyst}")
                    if hasattr(doc, 'adr_Nazwa') and doc.adr_Nazwa:
                        self.stdout.write(f"       Nazwa: {doc.adr_Nazwa}")
                    if hasattr(doc, 'adr_Ulica') and doc.adr_Ulica:
                        self.stdout.write(f"       Adres: {doc.adr_Ulica}, {doc.adr_Miejscowosc}")
                    if hasattr(doc, 'adr_Kod') and doc.adr_Kod:
                        self.stdout.write(f"       Kod: {doc.adr_Kod} {doc.adr_Poczta}")
                    else:
                        self.stdout.write(f"       Adres: Brak danych")
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Metoda get_zk() nie zwróciła dokumentów')
                )
                return False
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd testowania dok_Dokument: {str(e)}')
            )
            return False

    def test_dok_dokument_get_zd(self):
        """Test 9: dok_Dokument i get_zd"""
        self.stdout.write('\n--- Test 9: dok_Dokument i get_zd ---')
        try:
            self.stdout.write(
                self.style.SUCCESS('✓ Testuję metodę get_zd():')
            )
            zd_documents = dok_Dokument.dokument_objects.get_zd(limit=10)
            
            if zd_documents:
                self.stdout.write(f"  ✓ Pobrano {len(zd_documents)} dokumentów ZD:")
                for i, doc in enumerate(zd_documents, 1):
                    self.stdout.write(f"    {i}. {doc.dok_NrPelny} - {doc.document_type_name}")
                    self.stdout.write(f"       Magazyn: {doc.dok_MagId}")
                    if hasattr(doc, 'dok_DataWyst') and doc.dok_DataWyst:
                        self.stdout.write(f"       Data wystawienia: {doc.dok_DataWyst}")
                    if hasattr(doc, 'adr_Nazwa') and doc.adr_Nazwa:
                        self.stdout.write(f"       Nazwa: {doc.adr_Nazwa}")
                    if hasattr(doc, 'adr_Ulica') and doc.adr_Ulica:
                        self.stdout.write(f"       Adres: {doc.adr_Ulica}, {doc.adr_Miejscowosc}")
                    if hasattr(doc, 'adr_Kod') and doc.adr_Kod:
                        self.stdout.write(f"       Kod: {doc.adr_Kod} {doc.adr_Poczta}")
                    else:
                        self.stdout.write(f"       Adres: Brak danych")
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Metoda get_zd() nie zwróciła dokumentów')
                )
                return False
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd testowania get_zd: {str(e)}')
            )
            return False

    def test_get_zk_pozycje(self):
        """Test 10: get_zk_pozycje"""
        self.stdout.write('\n--- Test 10: dok_Dokument i get_zk_pozycje ---')
        try:
            # Pobierz 5 dokumentów ZK do testowania
            zk_documents = dok_Dokument.dokument_objects.get_zk(limit=5)
            
            if zk_documents:
                self.stdout.write(f"  ✓ Pobrano {len(zk_documents)} dokumentów ZK:")
                
                for i, doc in enumerate(zk_documents, 1):
                    self.stdout.write(f"    {i}. Dokument: {doc.dok_NrPelny} - {doc.document_type_name}")
                    self.stdout.write(f"       Magazyn: {doc.dok_MagId}")
                    if hasattr(doc, 'dok_DataWyst') and doc.dok_DataWyst:
                        self.stdout.write(f"       Data wystawienia: {doc.dok_DataWyst}")
                    
                    # Pobierz pozycje dla tego dokumentu
                    positions = dok_Dokument.dokument_objects.get_zk_pozycje(doc.dok_Id)
                    
                    if positions:
                        self.stdout.write(f"       ✓ Pozycje ({len(positions)}):")
                        for j, pos in enumerate(positions, 1):
                            self.stdout.write(f"         {j}. {pos['tw_Nazwa']} (ID: {pos['tw_Id']})")
                            self.stdout.write(f"            Status: {pos['ob_Status']}, Znak: {pos['ob_Znak']}")
                            self.stdout.write(f"            Stan: {pos['st_Stan']}, Zarezerwowany: {pos['st_StanRez']}")
                    else:
                        self.stdout.write(f"       ⚠ Brak pozycji")
                    
                    self.stdout.write("")  # Empty line for readability
                return True
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Brak dokumentów ZK do testowania pozycji')
                )
                return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd testowania get_zk_pozycje: {str(e)}')
            )
            return False

    def test_get_zd_pozycje(self):
        """Test 11: get_zd_pozycje"""
        self.stdout.write('\n--- Test 11: dok_Dokument i get_zd_pozycje ---')
        try:
            # Pobierz 5 dokumentów ZD do testowania
            zd_documents = dok_Dokument.dokument_objects.get_zd(limit=5)
            
            if zd_documents:
                self.stdout.write(f"  ✓ Pobrano {len(zd_documents)} dokumentów ZD:")
                
                for i, doc in enumerate(zd_documents, 1):
                    self.stdout.write(f"    {i}. Dokument: {doc.dok_NrPelny} - {doc.document_type_name}")
                    self.stdout.write(f"       Magazyn: {doc.dok_MagId}")
                    if hasattr(doc, 'dok_DataWyst') and doc.dok_DataWyst:
                        self.stdout.write(f"       Data wystawienia: {doc.dok_DataWyst}")
                    
                    # Pobierz pozycje dla tego dokumentu
                    positions = dok_Dokument.dokument_objects.get_zd_pozycje(doc.dok_Id)
                    
                    if positions:
                        self.stdout.write(f"       ✓ Pozycje ({len(positions)}):")
                        for j, pos in enumerate(positions, 1):
                            self.stdout.write(f"         {j}. {pos['tw_Nazwa']} (ID: {pos['tw_Id']})")
                            self.stdout.write(f"            Status: {pos['ob_Status']}, Znak: {pos['ob_Znak']}")
                            self.stdout.write(f"            Stan: {pos['st_Stan']}, Zarezerwowany: {pos['st_StanRez']}")
                    else:
                        self.stdout.write(f"       ⚠ Brak pozycji")
                    
                    self.stdout.write("")  # Empty line for readability
                return True
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Brak dokumentów ZD do testowania pozycji')
                )
                return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Błąd testowania get_zd_pozycje: {str(e)}')
            )
            return False

    def handle(self, *args, **options):
        # Check if --all flag is used
        if options.get('all'):
            self.stdout.write('Uruchamianie wszystkich testów...')
            tests = [
                self.test_database_connection,
                self.test_towar_table,
                self.test_stan_table,
                self.test_get_product_by_id,
                self.test_get_product_by_symbol,
                self.test_get_products_with_stock,
                self.test_get_product_by_id_manager,
                self.test_dok_dokument_get_zk,
                self.test_dok_dokument_get_zd,
                self.test_get_zk_pozycje,
                self.test_get_zd_pozycje
            ]
            
            results = []
            for test in tests:
                try:
                    result = test()
                    results.append(result)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Błąd w teście: {str(e)}'))
                    results.append(False)
            
            # Summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('PODSUMOWANIE TESTOW'))
            self.stdout.write('='*50)
            passed = sum(results)
            total = len(results)
            self.stdout.write(f'Przeszło: {passed}/{total}')
            if passed == total:
                self.stdout.write(self.style.SUCCESS('✓ Wszystkie testy przeszły pomyślnie!'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ {total - passed} testów nie przeszło'))
            return

        # Interactive mode
        while True:
            self.display_menu()
            choice = self.get_user_choice()
            
            if choice is None:
                self.stdout.write(self.style.SUCCESS('Do widzenia!'))
                break
            
            # Execute selected test
            test_methods = {
                1: self.test_database_connection,
                2: self.test_towar_table,
                3: self.test_stan_table,
                4: lambda: self.test_get_product_by_id(options.get('towar_id')),
                5: lambda: self.test_get_product_by_symbol(options.get('symbol')),
                6: self.test_get_products_with_stock,
                7: self.test_get_product_by_id_manager,
                8: self.test_dok_dokument_get_zk,
                9: self.test_dok_dokument_get_zd,
                10: self.test_get_zk_pozycje,
                11: self.test_get_zd_pozycje
            }
            
            if choice in test_methods:
                try:
                    test_methods[choice]()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Błąd w teście: {str(e)}'))
            else:
                self.stdout.write(self.style.ERROR('Nieprawidłowy wybór'))
            
            # Continue to next iteration (menu will be displayed again) 