from django.db import models
from django.db import connections
from django.conf import settings
from typing import Optional
from enum import Enum


class DocumentType(Enum):
    """Enumeration for document types in Subiekt"""
    FZ = 1
    FS = 2
    KFZ = 5
    KFS = 6
    MM = 9
    PZ = 10
    WZ = 11
    PW = 12
    RW = 13
    ZW = 14
    ZD = 15
    ZK = 16
    PA = 21
    IW = 29
    ZPZ = 35
    ZWZ = 36
    FM = 62


class DocumentSubtype(Enum):
    """Enumeration for document subtypes in Subiekt"""
    FZr_FSd_KFZn_KFSn_PZa_WZa_ZWn_PAf = 1
    FZz_FSz_PZv_WZv_PAi = 2
    FSzal_PZk_WZk_PAk = 3


class SubiektManager(models.Manager):
    def get_products_with_stock(self, limit: int = 10) -> list['tw_Towar']:
        """
        Fetches products from Subiekt along with their stock levels
        using a raw SQL query for performance.
        Returns a list of tw_Towar objects with stock information.
        If limit=0, returns all products (no limit).
        """
        mag_id = getattr(settings, 'SUBIEKT_MAGAZYN_ID', 2)
        
        # Build TOP clause conditionally
        top_clause = f"TOP {limit}" if limit > 0 else ""
        
        query = f"""
            SELECT {top_clause}
                t.tw_Id,
                t.tw_Symbol,
                t.tw_Nazwa,
                t.tw_Opis,
                ISNULL(s.st_Stan, 0) as st_Stan,
                ISNULL(s.st_StanRez, 0) as st_StanRez,
                ISNULL(g.grt_Nazwa, '') as grt_Nazwa
            FROM [dbo].[tw__Towar] t
            LEFT JOIN [dbo].[tw_Stan] s ON t.tw_Id = s.st_TowId AND s.st_MagId = %s
            LEFT JOIN [dbo].[sl_GrupaTw] g ON t.tw_IdGrupa = g.grt_Id
            ORDER BY t.tw_Id
        """
        
        with connections['subiekt'].cursor() as cursor:
            cursor.execute(query, [mag_id])
            
            products = []
            for row in cursor.fetchall():
                product = tw_Towar(
                    tw_Id=row[0],
                    tw_Symbol=row[1],
                    tw_Nazwa=row[2],
                    tw_Opis=row[3] or ""
                )
                
                # Add stock information as attributes
                product.st_Stan = float(row[4])
                product.st_StanRez = float(row[5])
                product.grt_Nazwa = row[6] or ""
                
                products.append(product)
            
            return products

    def get_product_by_id(self, product_id: int) -> Optional['tw_Towar']:
        """
        Fetches a single product by ID with stock information using a raw SQL query for performance.
        Returns a tw_Towar object or None if not found.
        """
        mag_id = getattr(settings, 'SUBIEKT_MAGAZYN_ID', 2)
        
        query = """
            SELECT 
                t.tw_Id,
                t.tw_Symbol,
                t.tw_Nazwa,
                t.tw_Opis,
                ISNULL(s.st_Stan, 0) as st_Stan,
                ISNULL(s.st_StanRez, 0) as st_StanRez,
                ISNULL(g.grt_Nazwa, '') as grt_Nazwa
            FROM [dbo].[tw__Towar] t
            LEFT JOIN [dbo].[tw_Stan] s ON t.tw_Id = s.st_TowId AND s.st_MagId = %s
            LEFT JOIN [dbo].[sl_GrupaTw] g ON t.tw_IdGrupa = g.grt_Id
            WHERE t.tw_Id = %s
        """
        
        with connections['subiekt'].cursor() as cursor:
            cursor.execute(query, [mag_id, product_id])
            row = cursor.fetchone()
            
            if row is None:
                return None
                
            # Create and return a tw_Towar object
            product = tw_Towar(
                tw_Id=row[0],
                tw_Symbol=row[1],
                tw_Nazwa=row[2],
                tw_Opis=row[3] or ""
            )
            
            # Add stock information as attributes
            product.st_Stan = float(row[4])
            product.st_StanRez = float(row[5])
            product.grt_Nazwa = row[6] or ""
            
            return product


class DokumentManager(models.Manager):
    def _get_documents(self, doc_type: int, limit: int = 10) -> list['dok_Dokument']:
        """
        Common method to fetch documents with contractor and address information.
        """
        # Build TOP clause conditionally
        top_clause = f"TOP {limit}" if limit > 0 else ""
        
        query = f"""
            SELECT {top_clause}
                d.dok_Id,
                d.dok_Typ,
                d.dok_Podtyp,
                d.dok_MagId,
                d.dok_Nr,
                d.dok_NrRoz,
                d.dok_NrPelny,
                d.dok_NrPelnyOryg,
                d.dok_DoDokId,
                d.dok_DoDokNrPelny,
                d.dok_PlatnikId,
                d.dok_PlatnikAdreshId,
                d.dok_OdbiorcaId,
                d.dok_OdbiorcaAdreshId,
                d.dok_DataWyst,
                d.dok_DataMag,
                d.dok_PlatTermin,
                a.adr_Nazwa,
                a.adr_NazwaPelna,
                a.adr_Ulica,
                a.adr_Miejscowosc,
                a.adr_Kod,
                a.adr_Poczta,
                a.adr_Adres
            FROM [dbo].[dok__Dokument] d
            LEFT JOIN [dbo].[adr__Ewid] a ON d.dok_OdbiorcaId = a.adr_IdObiektu
            WHERE d.dok_Typ = %s AND a.adr_TypAdresu = 1
            ORDER BY d.dok_DataWyst DESC, d.dok_Id DESC
        """
        
        with connections['subiekt'].cursor() as cursor:
            cursor.execute(query, [doc_type])
            
            documents = []
            for row in cursor.fetchall():
                document = dok_Dokument(
                    dok_Id=row[0],
                    dok_Typ=row[1],
                    dok_Podtyp=row[2],
                    dok_MagId=row[3],
                    dok_Nr=row[4],
                    dok_NrRoz=row[5],
                    dok_NrPelny=row[6],
                    dok_NrPelnyOryg=row[7],
                    dok_DoDokId=row[8],
                    dok_DoDokNrPelny=row[9],
                    dok_PlatnikId=row[10],
                    dok_PlatnikAdreshId=row[11],
                    dok_OdbiorcaId=row[12],
                    dok_OdbiorcaAdreshId=row[13]
                )
                
                # Add document dates as attributes
                document.dok_DataWyst = row[14]
                document.dok_DataMag = row[15]
                document.dok_PlatTermin = row[16]
                
                # Add address information as attributes
                document.adr_Nazwa = row[17]
                document.adr_NazwaPelna = row[18]
                document.adr_Ulica = row[19]
                document.adr_Miejscowosc = row[20]
                document.adr_Kod = row[21]
                document.adr_Poczta = row[22]
                document.adr_Adres = row[23]
                
                documents.append(document)
            
            return documents

    def get_zk(self, limit: int = 10) -> list['dok_Dokument']:
        """
        Fetches ZK documents (type 16) from Subiekt using a raw SQL query for performance.
        Returns a list of dok_Dokument objects with contractor and address information.
        If limit=0, returns all ZK documents (no limit).
        """
        return self._get_documents(DocumentType.ZK.value, limit)

    def get_zd(self, limit: int = 10) -> list['dok_Dokument']:
        """
        Fetches ZD documents (type 15) from Subiekt using a raw SQL query for performance.
        Returns a list of dok_Dokument objects with contractor and address information.
        If limit=0, returns all ZD documents (no limit).
        """
        return self._get_documents(DocumentType.ZD.value, limit)

    def get_zk_pozycje(self, zk_number: int) -> list[dict]:
        """
        Fetches all document positions/items for a specific ZK document.
        Returns a list of dictionaries with position information.
        """
        return self._get_document_positions(zk_number)

    def get_zd_pozycje(self, zd_number: int) -> list[dict]:
        """
        Fetches all document positions/items for a specific ZD document.
        Returns a list of dictionaries with position information.
        """
        return self._get_document_positions(zd_number)

    def _get_document_positions(self, doc_number: int) -> list[dict]:
        """
        Common method to fetch document positions/items for any document.
        Returns a list of dictionaries with position information including stock.
        """
        mag_id = getattr(settings, 'SUBIEKT_MAGAZYN_ID', 2)
        
        query = """
            SELECT 
                p.ob_Id,
                p.ob_DoId,
                p.ob_Znak,
                p.ob_Status,
                p.ob_DokHanId,
                p.ob_DokMagId,
                p.ob_TowId,
                t.tw_Id,
                t.tw_Nazwa,
                ISNULL(s.st_Stan, 0) as st_Stan,
                ISNULL(s.st_StanRez, 0) as st_StanRez
            FROM [dbo].[dok_Pozycja] p
            LEFT JOIN [dbo].[tw__Towar] t ON t.tw_Id = p.ob_TowId
            LEFT JOIN [dbo].[tw_Stan] s ON t.tw_Id = s.st_TowId AND s.st_MagId = %s
            WHERE p.ob_DokHanId = %s
        """
        
        with connections['subiekt'].cursor() as cursor:
            cursor.execute(query, [mag_id, doc_number])
            
            positions = []
            for row in cursor.fetchall():
                position = {
                    'ob_Id': row[0],
                    'ob_DoId': row[1],
                    'ob_Znak': row[2],
                    'ob_Status': row[3],
                    'ob_DokHanId': row[4],
                    'ob_DokMagId': row[5],
                    'ob_TowId': row[6],
                    'tw_Id': row[7],
                    'tw_Nazwa': row[8] or "",
                    'st_Stan': float(row[9]),
                    'st_StanRez': float(row[10])
                }
                positions.append(position)
            
            return positions


class tw_Towar(models.Model):
    """
    Model dla tabeli [dbo].[tw__Towar] w bazie danych Subiekt
    Odpowiada tabeli towarów w systemie Subiekt GT
    """
    
    # Pole ID z tabeli Subiekt
    tw_Id = models.AutoField(primary_key=True, db_column='tw_Id')
    
    # Nazwa towaru
    tw_Nazwa = models.CharField(
        max_length=200, 
        verbose_name="Nazwa towaru",
        db_column='tw_Nazwa'
    )
    
    # Symbol towaru (kod)
    tw_Symbol = models.CharField(
        max_length=50, 
        verbose_name="Symbol towaru",
        db_column='tw_Symbol'
    )
    
    # Opis towaru
    tw_Opis = models.TextField(
        blank=True, 
        verbose_name="Opis towaru",
        db_column='tw_Opis'
    )
    
    objects = models.Manager()
    subiekt_objects = SubiektManager()

    class Meta:
        managed = False  # Django nie będzie zarządzać tą tabelą
        db_table = '[dbo].[tw__Towar]'  # Pełna nazwa tabeli w MSSQL
        verbose_name = "Towar Subiekt"
        verbose_name_plural = "Towary Subiekt"
        # Używamy bazy danych 'subiekt'
        app_label = 'subiekt'
    
    def __str__(self):
        return f"{self.tw_Symbol} - {self.tw_Nazwa}"
    
    def save(self, *args, **kwargs):
        """Prevent saving - this is a read-only model"""
        raise PermissionError("Cannot save to read-only Subiekt database")
    
    def delete(self, *args, **kwargs):
        """Prevent deletion - this is a read-only model"""
        raise PermissionError("Cannot delete from read-only Subiekt database")


class tw_Cena(models.Model):
    """
    Model dla tabeli cen w bazie danych Subiekt
    Odpowiada tabeli cen towarów w systemie Subiekt GT
    """
    
    # Pole ID z tabeli Subiekt
    tc_Id = models.AutoField(primary_key=True, db_column='tc_Id')
    
    # Klucz obcy do modelu tw_Towar
    tc_IdTowar = models.ForeignKey(
        tw_Towar,
        on_delete=models.CASCADE,
        verbose_name="Towar",
        db_column='tc_IdTowar'
    )
    
    class Meta:
        managed = False  # Django nie będzie zarządzać tą tabelą
        db_table = '[dbo].[tw_Cena]'  # Pełna nazwa tabeli w MSSQL
        verbose_name = "Cena Subiekt"
        verbose_name_plural = "Ceny Subiekt"
        # Używamy bazy danych 'subiekt'
        app_label = 'subiekt'
    
    def __str__(self):
        return f"Cena dla {self.tc_IdTowar} - {self.tc_Id}"
    
    def save(self, *args, **kwargs):
        """Prevent saving - this is a read-only model"""
        raise PermissionError("Cannot save to read-only Subiekt database")
    
    def delete(self, *args, **kwargs):
        """Prevent deletion - this is a read-only model"""
        raise PermissionError("Cannot delete from read-only Subiekt database")


class tw_Stan(models.Model):
    """
    Model dla tabeli stanów magazynowych w bazie danych Subiekt
    Odpowiada tabeli stanów towarów w systemie Subiekt GT
    """

    # ID towaru (klucz obcy do tw_Towar)
    st_TowId = models.ForeignKey(
        tw_Towar,
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name="Towar",
        db_column='st_TowId',
        related_name='stany'
    )
    
    # ID magazynu (domyślnie 2)
    st_MagId = models.IntegerField(
        verbose_name="ID magazynu",
        db_column='st_MagId',
        default=2
    )
    
    # Stan magazynowy
    st_Stan = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Stan magazynowy",
        db_column='st_Stan'
    )
    
    # Stan minimalny
    st_StanMin = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Stan minimalny",
        db_column='st_StanMin'
    )
    
    # Stan zarezerwowany
    st_StanRez = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Stan zarezerwowany",
        db_column='st_StanRez'
    )
    
    # Stan maksymalny
    st_StanMax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Stan maksymalny",
        db_column='st_StanMax'
    )
    
    class Meta:
        managed = False  # Django nie będzie zarządzać tą tabelą
        db_table = '[dbo].[tw_Stan]'  # Pełna nazwa tabeli w MSSQL
        verbose_name = "Stan magazynowy Subiekt"
        verbose_name_plural = "Stany magazynowe Subiekt"
        # Używamy bazy danych 'subiekt'
        app_label = 'subiekt'
        #unique_together = (('st_TowId', 'st_MagId'),) # Defines the composite primary key to Django
    
    def __str__(self):
        return f"Stan towaru {self.st_TowId} w magazynie {self.st_MagId}: {self.st_Stan}"
    
    def save(self, *args, **kwargs):
        """Prevent saving - this is a read-only model"""
        raise PermissionError("Cannot save to read-only Subiekt database")
    
    def delete(self, *args, **kwargs):
        """Prevent deletion - this is a read-only model"""
        raise PermissionError("Cannot delete from read-only Subiekt database")


class dok_Dokument(models.Model):
    """
    Model dla tabeli dokumentów w bazie danych Subiekt
    Odpowiada tabeli dokumentów w systemie Subiekt GT
    """
    
    # Pole ID z tabeli Subiekt
    dok_Id = models.AutoField(primary_key=True, db_column='dok_Id')
    
    # Typ dokumentu
    dok_Typ = models.CharField(
        max_length=50, 
        verbose_name="Typ dokumentu",
        db_column='dok_Typ'
    )
    
    # Podtyp dokumentu
    dok_Podtyp = models.CharField(
        max_length=50, 
        verbose_name="Podtyp dokumentu",
        db_column='dok_Podtyp'
    )
    
    # ID magazynu
    dok_MagId = models.IntegerField(
        verbose_name="ID magazynu",
        db_column='dok_MagId'
    )
    
    # Numer dokumentu
    dok_Nr = models.CharField(
        max_length=50, 
        verbose_name="Numer dokumentu",
        db_column='dok_Nr'
    )
    
    # Numer rozliczenia
    dok_NrRoz = models.CharField(
        max_length=50, 
        verbose_name="Numer rozliczenia",
        db_column='dok_NrRoz'
    )
    
    # Numer pełny
    dok_NrPelny = models.CharField(
        max_length=100, 
        verbose_name="Numer pełny",
        db_column='dok_NrPelny'
    )
    
    # Numer pełny oryginalny
    dok_NrPelnyOryg = models.CharField(
        max_length=100, 
        verbose_name="Numer pełny oryginalny",
        db_column='dok_NrPelnyOryg'
    )
    
    # ID dokumentu do
    dok_DoDokId = models.IntegerField(
        verbose_name="ID dokumentu do",
        db_column='dok_DoDokId',
        null=True,
        blank=True
    )
    
    # Numer pełny dokumentu do
    dok_DoDokNrPelny = models.CharField(
        max_length=100, 
        verbose_name="Numer pełny dokumentu do",
        db_column='dok_DoDokNrPelny',
        null=True,
        blank=True
    )
    
    # Data wystawienia dokumentu do
    dok_DoDokDataWyst = models.DateField(
        verbose_name="Data wystawienia dokumentu do",
        db_column='dok_DoDokDataWyst',
        null=True,
        blank=True
    )
    
    # Miejsce wystawienia
    dok_MscWyst = models.CharField(
        max_length=100, 
        verbose_name="Miejsce wystawienia",
        db_column='dok_MscWyst',
        null=True,
        blank=True
    )
    
    # Data wystawienia
    dok_DataWyst = models.DateField(
        verbose_name="Data wystawienia",
        db_column='dok_DataWyst',
        null=True,
        blank=True
    )
    
    # Data magazynowa
    dok_DataMag = models.DateField(
        verbose_name="Data magazynowa",
        db_column='dok_DataMag',
        null=True,
        blank=True
    )
    
    # Data otrzymania
    dok_DataOtrzym = models.DateField(
        verbose_name="Data otrzymania",
        db_column='dok_DataOtrzym',
        null=True,
        blank=True
    )
    
    # ID płatnika
    dok_PlatnikId = models.IntegerField(
        verbose_name="ID płatnika",
        db_column='dok_PlatnikId',
        null=True,
        blank=True
    )
    
    # ID adresu płatnika
    dok_PlatnikAdreshId = models.IntegerField(
        verbose_name="ID adresu płatnika",
        db_column='dok_PlatnikAdreshId',
        null=True,
        blank=True
    )
    
    # ID odbiorcy
    dok_OdbiorcaId = models.IntegerField(
        verbose_name="ID odbiorcy",
        db_column='dok_OdbiorcaId',
        null=True,
        blank=True
    )
    
    # ID adresu odbiorcy
    dok_OdbiorcaAdreshId = models.IntegerField(
        verbose_name="ID adresu odbiorcy",
        db_column='dok_OdbiorcaAdreshId',
        null=True,
        blank=True
    )
    
    # ID płatności
    dok_PlatId = models.IntegerField(
        verbose_name="ID płatności",
        db_column='dok_PlatId',
        null=True,
        blank=True
    )
    
    # Termin płatności
    dok_PlatTermin = models.DateField(
        verbose_name="Termin płatności",
        db_column='dok_PlatTermin',
        null=True,
        blank=True
    )
    
    # Wystawił
    dok_Wystawil = models.CharField(
        max_length=100, 
        verbose_name="Wystawił",
        db_column='dok_Wystawil',
        null=True,
        blank=True
    )
    
    # Odebrał
    dok_Odebral = models.CharField(
        max_length=100, 
        verbose_name="Odebrał",
        db_column='dok_Odebral',
        null=True,
        blank=True
    )
    
    # ID personelu
    dok_PersonelId = models.IntegerField(
        verbose_name="ID personelu",
        db_column='dok_PersonelId',
        null=True,
        blank=True
    )
    
    class Meta:
        managed = False  # Django nie będzie zarządzać tą tabelą
        db_table = '[dbo].[dok__Dokument]'  # Pełna nazwa tabeli w MSSQL
        verbose_name = "Dokument Subiekt"
        verbose_name_plural = "Dokumenty Subiekt"
        # Używamy bazy danych 'subiekt'
        app_label = 'subiekt'
    
    objects = models.Manager()
    dokument_objects = DokumentManager()
    
    def __str__(self):
        return f"{self.dok_NrPelny} - {self.dok_Typ}"
    
    @property
    def document_type_name(self) -> str:
        """Returns the human-readable name of the document type"""
        try:
            return DocumentType(self.dok_Typ).name
        except ValueError:
            return f"Unknown({self.dok_Typ})"
    
    @property
    def document_subtype_name(self) -> str:
        """Returns the human-readable name of the document subtype"""
        try:
            return DocumentSubtype(self.dok_Podtyp).name
        except ValueError:
            return f"Unknown({self.dok_Podtyp})"
    
    def save(self, *args, **kwargs):
        """Prevent saving - this is a read-only model"""
        raise PermissionError("Cannot save to read-only Subiekt database")
    
    def delete(self, *args, **kwargs):
        """Prevent deletion - this is a read-only model"""
        raise PermissionError("Cannot delete from read-only Subiekt database")
