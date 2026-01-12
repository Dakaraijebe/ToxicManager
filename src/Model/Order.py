class Order:
    def __init__(self, id, client_id, material_id, quantity, total_price, date):
        self.id = id
        self.client_id = client_id
        self.material_id = material_id
        self.quantity = quantity
        self.total_price = total_price
        self.date = date