
from dataclasses import dataclass, field


@dataclass
class Dogodek:
    id: str
    api_id: str
    naziv: str
    vrsta: str
    datum: str
    cas: str
    opis: str
    rektascenzija: float
    deklinacija: float
    objekti: list[str] = field(default_factory=list)
    zacetek_okna: str | None = None
    konec_okna: str | None = None


@dataclass
class Lokacija:
    id: str
    osm_id: str
    osm_tip: str
    kategorija: str
    sirina: float
    dolzina: float
    naziv: str | None = None


@dataclass
class Vreme:
    vir: str
    cas_vremenskega_podatka: str
    oblacnost: int
    padavine: float
    hitrost_vetra: float
    sirina_vremenske_tocke: float
    dolzina_vremenske_tocke: float
    vidljivost: float | None = None


@dataclass
class Opazovanje:
    id: str
    dogodek_id: str
    lokacija_id: str
    datum: str
    cas: str
    casovni_pas: str
    vrsta_podatkov: str
    vreme: Vreme | None = None
