"""inventory system"""
import json

class Product:
    def __init__(self,name,price,quantity):
        self.name=name
        self.price=price
        self.quantity=quantity
    
    def get_total_value(self):
        return self.price*self.quantity
    
    def update_quantity(self,amount):
        self.quantity=self.quantity+amount
        if self.quantity<0:
            self.quantity=0

class Inventory:
    def __init__(self):
        self.products={}
    
    def add_product(self,product):
        self.products[product.name]=product
    
    def remove_product(self,name):
        del self.products[name]
    
    def get_product(self,name):
        return self.products[name]
    
    def calculate_total_inventory_value(self):
        total=0
        for name in self.products:
            total=total+self.products[name].get_total_value()
        return total
    
    def find_low_stock(self,threshold):
        low_stock=[]
        for name in self.products:
            if self.products[name].quantity<threshold:
                low_stock.append(name)
        return low_stock
    
    def apply_discount(self,name,percent):
        product=self.products[name]
        product.price=product.price-(product.price*percent/100)
    
    def restock(self,name,amount):
        self.products[name].update_quantity(amount)
    
    def export_to_json(self,filename):
        data={}
        for name in self.products:
            p=self.products[name]
            data[name]={"price":p.price,"quantity":p.quantity}
        f=open(filename,"w")
        json.dump(data,f)
        f.close()
    
    def import_from_json(self,filename):
        f=open(filename,"r")
        data=json.load(f)
        f.close()
        for name in data:
            self.add_product(Product(name,data[name]["price"],data[name]["quantity"]))

def process_order(inventory,order_items):
    """process customer order"""
    total=0
    for item in order_items:
        name=item["name"]
        qty=item["quantity"]
        product=inventory.get_product(name)
        if product.quantity>=qty:
            product.update_quantity(-qty)
            total=total+product.price*qty
        else:
            print("Not enough stock for "+name)
    return total

if __name__=="__main__":
    inv=Inventory()
    inv.add_product(Product("Laptop",999.99,10))
    inv.add_product(Product("Mouse",29.99,50))
    inv.add_product(Product("Keyboard",79.99,30))
    print("Total inventory value:",inv.calculate_total_inventory_value())
    print("Low stock items:",inv.find_low_stock(20))
