"""Value object for F1 track name validation and normalization with rich media data."""
from typing import Dict, Any, Optional
import random


class TrackName:
    """Immutable value object representing an F1 track with rich media data."""
    
    # Complete F1 track data with images and flags
    TRACK_DATA = {
        'bahrain': {
            'country': 'Bahrain',
            'name': 'Bahrain International Circuit',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244985/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Bahrain_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244973/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/bahrain-flag.png.transform/1col/image.png'
        },
        'saudi': {
            'country': 'Saudi Arabia',
            'name': 'Jeddah Corniche Circuit',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244985/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Saudi_Arabia_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244973/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/saudi-arabia-flag.png.transform/1col/image.png'
        },
        'australia': {
            'country': 'Australia',
            'name': 'Albert Park Circuit',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244985/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Australia_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/australia-flag.png.transform/1col/image.png'
        },
        'baku': {
            'country': 'Azerbaijan',
            'name': 'Baku City Circuit',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244987/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Baku_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244975/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/azerbaijan-flag.png.transform/1col/image.png'
        },
        'miami': {
            'country': 'USA (Miami)',
            'name': 'Miami International Autodrome',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244985/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Miami_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/united-states-of-america-flag.png.transform/1col/image.png'
        },
        'imola': {
            'country': 'Italy (Imola)',
            'name': 'Autodromo Enzo e Dino Ferrari',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244984/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Emilia_Romagna_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244973/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/italy-flag.png.transform/1col/image.png'
        },
        'monaco': {
            'country': 'Monaco',
            'name': 'Circuit de Monaco',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244984/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Monoco_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244972/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/monaco-flag.png.transform/1col/image.png'
        },
        'spain': {
            'country': 'Spain',
            'name': 'Circuit de Barcelona-Catalunya',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244986/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Spain_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244972/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/spain-flag.png.transform/1col/image.png'
        },
        'canada': {
            'country': 'Canada',
            'name': 'Circuit Gilles-Villeneuve',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Canada_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/canada-flag.png.transform/1col/image.png'
        },
        'austria': {
            'country': 'Austria',
            'name': 'Red Bull Ring',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Austria_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/austria-flag.png.transform/1col/image.png'
        },
        'silverstone': {
            'country': 'United Kingdom',
            'name': 'Silverstone Circuit',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Great_Britain_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/united-kingdom-flag.png.transform/1col/image.png'
        },
        'hungary': {
            'country': 'Hungary',
            'name': 'Hungaroring',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Hungary_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/hungary-flag.png.transform/1col/image.png'
        },
        'spa': {
            'country': 'Belgium',
            'name': 'Circuit de Spa-Francorchamps',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Belgium_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/belgium-flag.png.transform/1col/image.png'
        },
        'netherlands': {
            'country': 'Netherlands',
            'name': 'Circuit Zandvoort',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244984/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Netherlands_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244975/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/netherlands-flag.png.transform/1col/image.png'
        },
        'monza': {
            'country': 'Italy',
            'name': 'Autodromo Nazionale Monza',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244987/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Italy_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244973/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/italy-flag.png.transform/1col/image.png'
        },
        'singapore': {
            'country': 'Singapore',
            'name': 'Marina Bay Street Circuit',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1683633963/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Singapore_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244974/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/singapore-flag.png.transform/1col/image.png'
        },
        'japan': {
            'country': 'Japan',
            'name': 'Suzuka International Racing Course',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677250050/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Japan_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244973/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/japan-flag.png.transform/1col/image.png'
        },
        'qatar': {
            'country': 'Qatar',
            'name': 'Lusail International Circuit',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244985/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Qatar_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244974/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/qatar-flag.png.transform/1col/image.png'
        },
        'usa': {
            'country': 'USA (Austin)',
            'name': 'Circuit of The Americas',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244984/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/USA_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244972/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/united-states-of-america-flag.png.transform/1col/image.png'
        },
        'mexico': {
            'country': 'Mexico',
            'name': 'Autódromo Hermanos Rodríguez',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Mexico_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/mexico-flag.png.transform/1col/image.png'
        },
        'brazil': {
            'country': 'Brazil',
            'name': 'Autódromo José Carlos Pace',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Brazil_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/brazil-flag.png.transform/1col/image.png'
        },
        'las-vegas': {
            'country': 'USA (Las Vegas)',
            'name': 'Las Vegas Strip Circuit',
            'image_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677249930/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Las_Vegas_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/f_auto/q_auto/v1677244972/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/united-states-of-america-flag.png.transform/1col/image.png'
        },
        'abu-dhabi': {
            'country': 'UAE',
            'name': 'Yas Marina Circuit',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Abu_Dhabi_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/united-arab-emirates-flag.png.transform/1col/image.png'
        },
        'china': {
            'country': 'China',
            'name': 'Shanghai International Circuit',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/China_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/china-flag.png.transform/1col/image.png'
        },
        'france': {
            'country': 'France',
            'name': 'Circuit Paul Ricard',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/France_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/france-flag.png.transform/1col/image.png'
        },
        'portugal': {
            'country': 'Portugal',
            'name': 'Autódromo Internacional do Algarve',
            'image_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Portugal_Circuit.png.transform/7col/image.png',
            'flag_url': 'https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/portugal-flag.png.transform/1col/image.png'
        }
    }
    
    # Legacy support - display names extracted from TRACK_DATA
    VALID_TRACKS = {key: data['name'] for key, data in TRACK_DATA.items()}
    
    # Alternative names/abbreviations
    ALIASES = {
        'cota': 'usa',
        'vegas': 'las-vegas',
        'jeddah': 'saudi',
        'albert-park': 'australia',
        'barcelona': 'spain',
        'catalunya': 'spain',
        'villeneuve': 'canada',
        'red-bull-ring': 'austria',
        'hungaroring': 'hungary',
        'spa-francorchamps': 'spa',
        'zandvoort': 'netherlands',
        'marina-bay': 'singapore',
        'suzuka': 'japan',
        'losail': 'qatar',
        'hermanos-rodriguez': 'mexico',
        'interlagos': 'brazil',
        'yas-marina': 'abu-dhabi'
    }
    
    def __init__(self, track_input: str):
        self._original_input = track_input.strip()
        self._normalized_name = self._normalize_track_name(self._original_input)
        
        if self._normalized_name not in self.TRACK_DATA:
            valid_options = list(self.TRACK_DATA.keys()) + list(self.ALIASES.keys())
            raise ValueError(
                f"Invalid track name: '{track_input}'. "
                f"Valid options: {', '.join(sorted(valid_options))}"
            )
    
    def _normalize_track_name(self, track_input: str) -> str:
        """Normalize track input to standard format."""
        normalized = track_input.lower().strip()
        normalized = normalized.replace(' ', '-')
        normalized = normalized.replace('_', '-')
        
        # Check if it's an alias first
        if normalized in self.ALIASES:
            return self.ALIASES[normalized]
        
        # Check if it's already a valid track key
        if normalized in self.TRACK_DATA:
            return normalized
        
        # Try to find partial matches
        for key in self.TRACK_DATA.keys():
            if normalized in key or key in normalized:
                return key
        
        return normalized
    
    @property
    def key(self) -> str:
        """Get the normalized key for this track."""
        return self._normalized_name
    
    @property
    def display_name(self) -> str:
        """Get the full official display name."""
        return self.TRACK_DATA[self._normalized_name]['name']
    
    @property
    def country(self) -> str:
        """Get the country/region for this track."""
        return self.TRACK_DATA[self._normalized_name]['country']
    
    @property
    def image_url(self) -> str:
        """Get the official circuit layout image URL."""
        return self.TRACK_DATA[self._normalized_name]['image_url']
    
    @property
    def flag_url(self) -> str:
        """Get the country flag image URL."""
        return self.TRACK_DATA[self._normalized_name]['flag_url']
    
    @property
    def track_data(self) -> Dict[str, Any]:
        """Get all track data as dictionary."""
        return self.TRACK_DATA[self._normalized_name].copy()
    
    @property
    def short_name(self) -> str:
        """Get a short version of the track name."""
        return self._normalized_name.replace('-', ' ').title()
    
    def __str__(self) -> str:
        return self.short_name
    
    def __repr__(self) -> str:
        return f"TrackName('{self._original_input}')"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TrackName):
            return False
        return self._normalized_name == other._normalized_name
    
    def __hash__(self) -> int:
        return hash(self._normalized_name)
    
    @classmethod
    def get_all_valid_tracks(cls) -> list[str]:
        """Get all valid track options for help messages."""
        return sorted(list(cls.TRACK_DATA.keys()) + list(cls.ALIASES.keys()))
    
    @classmethod
    def get_random_track(cls) -> 'TrackName':
        """Get a random track for challenges or examples."""
        random_key = random.choice(list(cls.TRACK_DATA.keys()))
        return cls(random_key)
    
    @classmethod
    def get_all_track_data(cls) -> Dict[str, Dict[str, Any]]:
        """Get all track data for advanced use cases."""
        return cls.TRACK_DATA.copy()
