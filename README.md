# Regalator WMS

Regalator WMS to kompleksowy system zarządzania magazynem zbudowany w Django, zaprojektowany do zarządzania operacjami magazynowymi, w tym kompletacją, przyjęciami, zarządzaniem zapasami oraz integracją z systemem księgowym Subiekt GT.

## 🚀 Funkcje

### Podstawowe funkcje WMS
- **Zarządzanie zapasami**: Śledzenie produktów, lokalizacji i poziomów stanów
- **Operacje kompletacji**: Zarządzanie kompletacją zamówień klientów ze skanowaniem kodów kreskowych
- **Operacje przyjęć**: Obsługa dostaw od dostawców i procesów przyjęć
- **Grupy produktów**: Organizacja produktów w logiczne grupy
- **Zarządzanie lokalizacjami**: Zarządzanie lokalizacjami magazynowymi i strefami
- **Śledzenie zapasów**: Monitorowanie poziomów stanów w czasie rzeczywistym z ilościami zarezerwowanymi

### Integracja z Subiekt GT
- **Synchronizacja w czasie rzeczywistym**: Synchronizacja produktów i poziomów stanów z Subiekt GT
- **Dwukierunkowy przepływ danych**: Import produktów z Subiekt i aktualizacja poziomów stanów
- **Grupy produktów**: Automatyczne tworzenie i zarządzanie grupami produktów
- **Rekonciliacja zapasów**: Porównanie stanów WMS vs Subiekt

### Interfejs użytkownika
- **Nowoczesny interfejs Bootstrap**: Czysty, responsywny interfejs
- **Integracja HTMX**: Dynamiczne aktualizacje bez przeładowania stron
- **Powiadomienia Toast**: Informacje zwrotne dla użytkownika w czasie rzeczywistym
- **Skanowanie kodów kreskowych**: Przyjazny dla urządzeń mobilnych interfejs skanowania
- **Zaawansowane filtrowanie**: Potężne możliwości wyszukiwania i filtrowania

### Funkcje techniczne
- **Framework Django**: Solidny framework webowy
- **SQLite/PostgreSQL**: Elastyczne wsparcie dla baz danych
- **HTMX**: Nowoczesny AJAX bez złożoności JavaScript
- **Bootstrap 5**: Responsywny framework projektowy
- **Font Awesome**: Profesjonalne ikony

## 📋 Wymagania

### Wymagania systemowe
- Python 3.8+
- Django 4.2+
- SQLite lub PostgreSQL
- Sterowniki ODBC dla połączenia z Subiekt GT

### Zależności Python
- Django
- pyodbc (dla połączenia z Subiekt)
- Pillow (dla obsługi obrazów)
- django-crispy-forms (opcjonalnie)

## 🛠️ Instalacja

### 1. Sklonuj repozytorium
```bash
git clone https://github.com/yourusername/regalator.git
cd regalator
```

### 2. Utwórz środowisko wirtualne
```bash
python -m venv venv
source venv/bin/activate  # W systemie Windows: venv\Scripts\activate
```

### 3. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 4. Skonfiguruj bazę danych
```bash
cd regalator
python manage.py migrate
```

### 5. Utwórz superużytkownika
```bash
python manage.py createsuperuser
```

### 6. Skonfiguruj połączenie z Subiekt
Edytuj `regalator/settings.py` i skonfiguruj połączenie z bazą danych Subiekt:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'subiekt': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'twoja_baza_subiekt',
        'HOST': 'twoj_serwer',
        'USER': 'twoja_nazwa_uzytkownika',
        'PASSWORD': 'twoje_haslo',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}

# Konfiguracja Subiekt
SUBIEKT_MAGAZYN_ID = 2  # Domyślne ID magazynu
```

### 7. Uruchom serwer deweloperski
```bash
python manage.py runserver
```

Odwiedź http://127.0.0.1:8000/ aby uzyskać dostęp do aplikacji.

## 📁 Struktura projektu

```
regalator/
├── regalator/          # Główny projekt Django
│   ├── settings.py     # Ustawienia Django
│   ├── urls.py         # Główna konfiguracja URL
│   └── wsgi.py         # Konfiguracja WSGI
├── wms/                # Aplikacja WMS
│   ├── models.py       # Modele danych WMS
│   ├── views.py        # Widoki i logika WMS
│   ├── urls.py         # Routing URL WMS
│   └── templates/      # Szablony HTML
├── subiekt/            # Integracja z Subiekt
│   ├── models.py       # Modele danych Subiekt
│   └── routers.py      # Routing bazy danych
├── assets/             # Zarządzanie zasobami
│   ├── models.py       # Modele zasobów
│   └── views.py        # Widoki zasobów
├── media/              # Pliki przesłane przez użytkowników
├── static/             # Pliki statyczne
└── manage.py           # Skrypt zarządzania Django
```

## 🔧 Konfiguracja

### Zmienne środowiskowe
Utwórz plik `.env` w głównym katalogu projektu:

```env
DEBUG=True
SECRET_KEY=twoj-sekretny-klucz
DATABASE_URL=sqlite:///db.sqlite3
SUBIEKT_DATABASE_URL=twoj-ciag-polaczenia-subiekt
SUBIEKT_MAGAZYN_ID=2
```

### Integracja z Subiekt
1. Zainstaluj sterowniki ODBC dla SQL Server
2. Skonfiguruj połączenie z bazą danych w settings.py
3. Przetestuj połączenie używając komend zarządzania

## 🚀 Użytkowanie

### Komendy zarządzania

#### Synchronizuj produkty z Subiekt
```bash
python manage.py sync_subiekt
```

#### Synchronizuj konkretny produkt
```bash
python manage.py sync_subiekt --product-id 123
```

#### Załaduj dane demo
```bash
python manage.py load_demo_data
```

### Interfejs webowy

1. **Dashboard**: Przegląd operacji magazynowych
2. **Produkty**: Zarządzaj katalogiem produktów i synchronizuj z Subiekt
3. **Kompletacja**: Przetwarzaj zamówienia klientów ze skanowaniem kodów kreskowych
4. **Przyjęcia**: Obsługuj dostawy od dostawców
5. **Lokalizacje**: Zarządzaj lokalizacjami magazynowymi
6. **Stany**: Monitoruj poziomy zapasów

## 🔒 Bezpieczeństwo

### Wdrożenie produkcyjne
1. Ustaw `DEBUG=False` w produkcji
2. Użyj silnego `SECRET_KEY`
3. Skonfiguruj HTTPS
4. Ustaw odpowiednie uprawnienia bazy danych
5. Użyj zmiennych środowiskowych dla wrażliwych danych

### Bezpieczeństwo bazy danych
- Użyj dedykowanego użytkownika bazy danych z minimalnymi uprawnieniami
- Szyfruj połączenia z bazą danych
- Regularne kopie zapasowe
- Monitoruj logi dostępu

## 🧪 Testowanie

### Uruchom testy
```bash
python manage.py test
```

### Uruchom testy konkretnej aplikacji
```bash
python manage.py test wms
python manage.py test subiekt
```

## 📊 Monitorowanie

### Logi
- Logi aplikacji: `logs/regalator.log`
- Śledzenie błędów: Skonfiguruj z preferowanym serwisem
- Monitorowanie wydajności: Django Debug Toolbar (dewelopersko)

### Kontrole zdrowia
- Łączność z bazą danych
- Status połączenia z Subiekt
- Alerty poziomów stanów
- Monitorowanie statusu synchronizacji

## 🤝 Współtworzenie

### Konfiguracja deweloperska
1. Sforkuj repozytorium
2. Utwórz gałąź funkcjonalności
3. Wprowadź zmiany
4. Dodaj testy
5. Prześlij pull request

### Styl kodu
- Przestrzegaj PEP 8
- Używaj znaczących nazw zmiennych
- Dodawaj docstringi do funkcji
- Pisz testy dla nowych funkcji

## 📝 Licencja

Ten projekt jest licencjonowany na licencji MIT - zobacz plik [LICENSE](LICENSE) dla szczegółów.

## 🆘 Wsparcie

### Dokumentacja
- [Dokumentacja Django](https://docs.djangoproject.com/)
- [Dokumentacja HTMX](https://htmx.org/docs/)
- [Dokumentacja Bootstrap](https://getbootstrap.com/docs/)

### Problemy
- Zgłaszaj błędy przez GitHub Issues
- Żądaj funkcji przez GitHub Issues
- Zadawaj pytania przez GitHub Discussions

### Społeczność
- Dołącz do naszego serwera Discord
- Śledź nas na Twitterze
- Zapisz się do naszego newslettera

## 🔄 Historia zmian

### Wersja 1.0.0
- Początkowe wydanie
- Podstawowe funkcje WMS
- Integracja z Subiekt GT
- Interfejs napędzany HTMX
- UI Bootstrap 5

## 📞 Kontakt

- **Email**: support@regalator.com
- **Strona internetowa**: https://regalator.com
- **GitHub**: https://github.com/yourusername/regalator

---

**Stworzone z ❤️ przez zespół Regalator** 