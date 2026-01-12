class Client:
    def __init__(self, id, name, email, credit, signed_date=None):
        self.id = id
        self.name = name
        self.email = email
        self.credit = credit
        self.signed_date = signed_date

    def __str__(self):
        return f"Klient: {self.name} (Kredit: {self.credit})"