# Regalator WMS - System Zarządzania Magazynem

## Funkcjonalności

1. **Zamówienia klientów** - zarządzanie zamówieniami i ich statusami
2. **Zlecenia kompletacji (REG)** - tworzenie i zarządzanie zleceniami kompletacji
3. **Skanowanie kodów kreskowych** - kompletacja produktów przez skanowanie
4. **Zarządzanie produktami** - dodawanie, edycja i usuwanie produktów
5. **Zarządzanie lokalizacjami** - organizacja magazynu w lokalizacje
6. **Stany magazynowe** - śledzenie ilości produktów w lokalizacjach
7. **Zarządzanie użytkownikami** - system logowania i uprawnień

## Workflow kompletacji

1. **Utworzenie zamówienia** - klient składa zamówienie
2. **Tworzenie zlecenia kompletacji** - system tworzy REG (Zlecenie Kompletacji)
3. **Skanowanie lokalizacji** - operator skanuje kod lokalizacji
4. **Skanowanie produktu** - operator skanuje kod produktu
5. **Wprowadzenie ilości** - operator wprowadza ilość skompletowaną
6. **Zakończenie kompletacji** - system aktualizuje stany magazynowe

## Modele danych

### Zamówienia
- `CustomerOrder` - zamówienia klientów
- `OrderItem` - pozycje zamówień

### Kompletacja
- `PickingOrder` - zlecenia kompletacji (REG)
- `PickingItem` - pozycje kompletacji

### Magazyn
- `Product` - produkty z kodami kreskowymi
- `Location` - lokalizacje magazynowe
- `Stock` - stany magazynowe (produkt + lokalizacja + ilość)

## Widoki i funkcjonalności

### Zamówienia
- Lista zamówień - przeglądanie i filtrowanie
- Szczegóły zamówienia - podgląd pozycji
- Utwórz REG - kliknij "Utwórz REG"

### Kompletacja
- Lista zleceń kompletacji - zarządzanie REG
- Szczegóły zlecenia - podgląd pozycji do kompletacji
- Skanowanie lokalizacji - wybór lokalizacji do kompletacji
- Skanowanie produktu - kompletacja konkretnego produktu
- Wprowadzenie ilości - potwierdzenie skompletowanej ilości

### Produkty i magazyn
- Lista produktów - zarządzanie produktami
- Stany magazynowe - przegląd ilości w lokalizacjach
- Lista lokalizacji - organizacja magazynu

## Instalacja i uruchomienie

1. **Sklonuj repozytorium**
```bash
git clone <repository-url>
cd regalator
```

2. **Utwórz środowisko wirtualne**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows
```

3. **Zainstaluj zależności**
```bash
pip install -r requirements.txt
```

4. **Wykonaj migracje**
```bash
python manage.py migrate
```

5. **Utwórz superużytkownika**
```bash
python manage.py createsuperuser
```

6. **Uruchom serwer**
```bash
python manage.py runserver
```

7. **Załaduj dane demo**
```bash
python manage.py load_demo_data
```

## Użycie

1. **Zaloguj się** do systemu
2. **Przejdź do zamówień** - wybierz zamówienie do kompletacji
3. **Utwórz REG** - kliknij "Utwórz REG"
4. **Rozpocznij kompletację** - kliknij "Rozpocznij kompletację"
5. **Skanuj lokalizację** - zeskanuj kod lokalizacji
6. **Skanuj produkt** - zeskanuj kod produktu
7. **Wprowadź ilość** - potwierdź skompletowaną ilość
8. **Kontynuuj** - powtórz dla kolejnych produktów
9. **Zakończ kompletację** - kliknij "Zakończ kompletację"

## Technologie

- **Django** - framework webowy
- **Bootstrap 5** - framework CSS
- **Font Awesome** - ikony
- **SQLite** - baza danych (można zmienić na PostgreSQL/MySQL)

## Struktura projektu

```
regalator/
├── wms/                    # Aplikacja WMS
│   ├── models.py          # Modele danych
│   ├── views.py           # Widoki
│   ├── urls.py            # Routing URL
│   ├── admin.py           # Panel administracyjny
│   └── templates/         # Szablony HTML
├── assets/                # Aplikacja zarządzania zasobami
│   ├── models.py          # Modele zasobów
│   ├── views.py           # Widoki zasobów
│   └── templates/         # Szablony zasobów
└── manage.py              # Skrypt zarządzania Django
``` 