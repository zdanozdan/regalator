# Instrukcja instalacji Regalator WMS

## 🚀 Szybka instalacja

### Dla Windows:
```cmd
install.bat
```
Lub dwukliknij na `install.bat` w Eksploratorze plików.

### Dla Linux/macOS:
```bash
./install.sh
```

## 📝 Szczegółowa instrukcja krok po kroku

### Krok 1: Pobierz kod
```bash
git clone https://github.com/yourusername/regalator.git
cd regalator
```

### Krok 2: Uruchom instalację

**Opcja A - Skrypt instalacyjny (zalecane):**
```bash
# Linux/macOS
python3 install.py

# Windows
python install.py
```

**Opcja B - Ręcznie:**
```bash
# 1. Utwórz venv
python -m venv venv

# 2. Aktywuj venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. Zainstaluj pakiety
pip install -r requirements.txt
```

### Krok 3: Uruchom migracje (BARDZO WAŻNE!)

```bash
# Aktywuj venv jeśli jeszcze nie aktywowane
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Przejdź do katalogu Django
cd regalator

# Uruchom migracje
python manage.py migrate
```

**⚠️ OSTRZEŻENIE:** Jeśli pominiesz ten krok, otrzymasz błędy typu:
- `no such column: wms_product.parent_id`
- `no such table: wms_productcode`
- `no such column: wms_location.barcode`

### Krok 4: Utwórz superużytkownika
```bash
python manage.py createsuperuser
```

Podaj:
- Nazwę użytkownika
- Email (opcjonalny)
- Hasło (2 razy)

### Krok 5: Uruchom serwer
```bash
python manage.py runserver
```

Otwórz przeglądarkę: http://127.0.0.1:8000/

## 🔧 Rozwiązywanie problemów

### Problem 1: "no such column: wms_product.parent_id"

**Przyczyna:** Baza danych jest stara i nie ma najnowszego schematu.

**Rozwiązanie - Start od nowa (zalecane):**

```bash
# 1. Usuń starą bazę
rm regalator/db.sqlite3           # Linux/macOS
del regalator\db.sqlite3          # Windows

# 2. Uruchom migracje ponownie
cd regalator
python manage.py migrate

# 3. Utwórz nowego superusera
python manage.py createsuperuser
```

**Rozwiązanie - Zaktualizuj bazę (zachowuje dane):**

```bash
cd regalator
python manage.py migrate
```

To powinno dodać brakujące kolumny do istniejącej bazy.

### Problem 2: "ModuleNotFoundError: No module named 'setuptools'"

**Przyczyna:** Próbujesz uruchomić `python setup.py` bezpośrednio.

**Rozwiązanie:**

```bash
# ❌ NIE UŻYWAJ:
python setup.py install

# ✅ ZAMIAST TEGO:
python install.py
```

Skrypt `install.py` używa tylko biblioteki standardowej Python i automatycznie zainstaluje setuptools w venv.

### Problem 3: Brak modułu Django

**Przyczyna:** Venv nie jest aktywowane lub pakiety nie zostały zainstalowane.

**Rozwiązanie:**

```bash
# 1. Aktywuj venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 2. Sprawdź czy Django jest zainstalowane
python -c "import django; print(django.VERSION)"

# 3. Jeśli nie, zainstaluj requirements
pip install -r requirements.txt
```

### Problem 4: Błędy podczas sync_zd lub sync_subiekt

**Przyczyny:**
- Baza danych nie jest zaktualizowana (brak migracji)
- Brak połączenia z Subiekt GT
- Błędna konfiguracja ODBC

**Rozwiązanie:**

```bash
# 1. Najpierw uruchom migracje!
cd regalator
python manage.py migrate

# 2. Sprawdź połączenie z Subiekt
python manage.py shell
>>> from django.db import connections
>>> connections['subiekt'].cursor()
>>> # Jeśli nie ma błędów, połączenie działa!

# 3. Test synchronizacji
python manage.py sync_subiekt --limit 10
```

### Problem 5: Port 8000 już zajęty

**Rozwiązanie:**

```bash
# Użyj innego portu
python manage.py runserver 8001

# Lub znajdź i zatrzymaj proces na porcie 8000
# Linux/macOS:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F
```

## 📦 Struktura plików instalacyjnych

- **install.py** - Główny skrypt instalacyjny (cross-platform)
- **install.sh** - Bash wrapper dla Linux/macOS
- **install.bat** - Batch wrapper dla Windows
- **setup.py** - Konfiguracja setuptools (nie uruchamiaj bezpośrednio!)
- **requirements.txt** - Lista zależności Python

## ✅ Checklist instalacji

- [ ] Python 3.8+ zainstalowany
- [ ] Git zainstalowany
- [ ] Sklonowane repozytorium
- [ ] Uruchomiony skrypt instalacyjny (`install.py` lub `install.sh`/`install.bat`)
- [ ] Venv utworzony i aktywowany
- [ ] Pakiety zainstalowane (`pip list` pokazuje Django, Pillow, etc.)
- [ ] Migracje uruchomione (`python manage.py migrate`)
- [ ] Superuser utworzony
- [ ] Serwer uruchomiony (`python manage.py runserver`)
- [ ] Aplikacja działa w przeglądarce (http://127.0.0.1:8000/)

## 💡 Najlepsze praktyki

1. **Zawsze uruchamiaj migracje** po sklonowaniu lub aktualizacji kodu
2. **Używaj venv** - nigdy nie instaluj pakietów globalnie
3. **Backup bazy danych** przed większymi zmianami
4. **Sprawdź .gitignore** - venv i db.sqlite3 są ignorowane
5. **Używaj install.py** zamiast setup.py dla pierwszej instalacji

## 📞 Potrzebujesz pomocy?

Jeśli nadal masz problemy:
1. Sprawdź [sekcję Troubleshooting w README.md](README.md#-troubleshooting)
2. Zgłoś issue na GitHub z pełnym traceback
3. Dołącz do community Discord

---

**Miłej pracy z Regalator WMS! 🎉**

