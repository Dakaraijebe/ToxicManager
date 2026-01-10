class Material:
    def __init__(self, id, name, price_per_kg, hazard_level, is_active):
        self.id = id
        self.name = name
        self.price_per_kg = price_per_kg
        self.hazard_level = hazard_level
        self.is_active = is_active

    def __str__(self):
        status = "AKTIVNÍ" if self.is_active else "NEAKTIVNÍ"
        return f"ID: {self.id} | {self.name} ({self.hazard_level}) | {self.price_per_kg} Kč | {status}"