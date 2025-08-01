# Aplikacja Subiekt Integration

Aplikacja do integracji z bazą danych Microsoft SQL Server Subiekt GT.

## Konfiguracja

### 1. Instalacja sterowników

```bash
pip install django-mssql-backend pyodbc
```

### 2. Konfiguracja bazy danych

W pliku `regalator/settings.py` zaktualizuj konfigurację bazy danych:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'subiekt': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'SubiektDB',  # Nazwa bazy danych Subiekt
        'USER': 'your_username',  # Nazwa użytkownika
        'PASSWORD': 'your_password',  # Hasło
        'HOST': 'your_server',  # Serwer MSSQL
        'PORT': '1433',  # Port MSSQL (domyślny)
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'unicode_results': True,
        },
    }
}

# Database routers
DATABASE_ROUTERS = ['subiekt.routers.SubiektRouter']
```

### 3. Sterowniki ODBC

Upewnij się, że masz zainstalowany sterownik ODBC dla SQL Server:

**Windows:**
- Microsoft ODBC Driver 17 for SQL Server

**macOS:**
```bash
# Instalacja przez Homebrew
brew install microsoft/mssql-release/mssql-tools

# Sprawdzenie zainstalowanych sterowników ODBC
odbcinst -j

# Sprawdzenie dostępnych sterowników
odbcinst -q -d

# Sprawdzenie konkretnego sterownika SQL Server
odbcinst -q -d | grep -i sql
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

#### Sprawdzanie sterowników ODBC na macOS:

1. **Sprawdzenie zainstalowanych sterowników:**
   ```bash
   odbcinst -j
   ```
   To polecenie pokaże ścieżki do plików konfiguracyjnych ODBC.

2. **Lista dostępnych sterowników:**
   ```bash
   odbcinst -q -d
   ```
   To polecenie wyświetli wszystkie zainstalowane sterowniki ODBC.

3. **Sprawdzenie sterownika SQL Server:**
   ```bash
   odbcinst -q -d | grep -i sql
   ```
   To polecenie wyszuka sterowniki zawierające "sql" w nazwie.

4. **Sprawdzenie konkretnego sterownika:**
   ```bash
   odbcinst -q -d | grep "ODBC Driver 17 for SQL Server"
   ```
   To polecenie sprawdzi czy jest zainstalowany sterownik wersji 17.

5. **Test połączenia z bazą danych:**
   ```bash
   # Sprawdzenie czy Python może połączyć się z bazą
   python -c "import pyodbc; print('pyodbc version:', pyodbc.version)"
   ```

#### Instalacja sterowników na macOS:

Jeśli sterowniki nie są zainstalowane:

```bash
# Instalacja przez Homebrew
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql17

# Lub instalacja bezpośrednio
curl https://packages.microsoft.com/keys/microsoft.asc | brew-key add -
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql17
```

## Modele

### Towar

Model dla tabeli `[dbo].[tw__Towar]` w bazie danych Subiekt:

- `tw_Id` - ID towaru (primary key)
- `tw_Symbol` - Symbol/kod towaru
- `tw_Nazwa` - Nazwa towaru
- `tw_Opis` - Opis towaru

## Testy

### Uruchomienie testów

```bash
# Wszystkie testy aplikacji subiekt
python manage.py test subiekt

# Konkretne testy
python manage.py test subiekt.tests.SubiektDatabaseTest
python manage.py test subiekt.tests.SubiektModelTest
```

### Testy połączenia z bazą danych

```bash
# Podstawowy test połączenia
python manage.py test_subiekt_connection

# Test z konkretnym ID towaru
python manage.py test_subiekt_connection --towar-id 123

# Test z konkretnym symbolem
python manage.py test_subiekt_connection --symbol "HYRAMIC HT A1"
```

## Router bazy danych

Aplikacja używa routera `SubiektRouter`, który kieruje wszystkie modele z aplikacji `subiekt` do bazy danych `subiekt`.

## Admin

Model `Towar` jest dostępny w panelu admin Django, ale operacje zapisu są wyłączone (dane pochodzą z Subiekt).

## Struktura aplikacji

```
subiekt/
├── __init__.py
├── admin.py                    # Panel admin (tylko odczyt)
├── apps.py                     # Konfiguracja aplikacji
├── models.py                   # Model Towar
├── routers.py                  # Router bazy danych
├── tests.py                    # Testy jednostkowe
├── README.md                   # Dokumentacja
└── management/
    └── commands/
        └── test_subiekt_connection.py  # Komenda testowa
```

## Funkcjonalności

### Testy jednostkowe

- **SubiektDatabaseTest** - testy połączenia z bazą danych
  - `test_database_connection()` - sprawdzenie połączenia
  - `test_towar_table_exists()` - sprawdzenie istnienia tabeli
  - `test_get_towar_by_id()` - pobieranie towaru po ID
  - `test_get_towar_by_symbol()` - pobieranie towaru po symbolu
  - `test_count_towary()` - liczenie towarów w bazie

- **SubiektModelTest** - testy modelu Towar
  - `test_towar_str_representation()` - reprezentacja string
  - `test_towar_properties()` - właściwości modelu
  - `test_towar_empty_description()` - obsługa pustego opisu

### Komenda management

- **test_subiekt_connection** - test połączenia i pobierania danych
  - Sprawdzenie połączenia z bazą danych
  - Sprawdzenie istnienia tabeli `[dbo].[tw__Towar]`
  - Pobieranie towarów po ID lub symbolu
  - Wyświetlanie przykładowych danych

## Bezpieczeństwo

- Model `Towar` jest tylko do odczytu (nie można modyfikować danych Subiekt)
- Połączenie używa konfiguracji z `settings.py`
- Router zapewnia izolację bazy danych

## Rozwiązywanie problemów

### Błąd połączenia z bazą danych

1. Sprawdź konfigurację w `settings.py`
2. Upewnij się, że sterownik ODBC jest zainstalowany
3. Sprawdź dostępność serwera MSSQL
4. Zweryfikuj nazwę użytkownika i hasło

### Błąd "Table does not exist"

1. Sprawdź czy tabela `[dbo].[tw__Towar]` istnieje w bazie Subiekt
2. Zweryfikuj nazwę tabeli w modelu `Towar`
3. Sprawdź uprawnienia użytkownika do tabeli

### Błąd sterownika ODBC

1. Zainstaluj odpowiedni sterownik dla swojego systemu
2. Sprawdź czy sterownik jest w ścieżce systemowej
3. Zweryfikuj wersję sterownika w konfiguracji Django 