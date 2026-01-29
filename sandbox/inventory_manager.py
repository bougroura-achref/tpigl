"""Inventory management system for tracking products and stock levels."""
import json
from typing import Dict, List, Optional


class Product:
    """Represents a product with name, price, and quantity.
    
    Attributes:
        name (str): The product name
        price (float): The product price
        quantity (int): The current stock quantity
    """
    
    def __init__(self, name: str, price: float, quantity: int) -> None:
        """Initialize a new product.
        
        Args:
            name: The product name
            price: The product price
            quantity: The initial stock quantity
        """
        self.name = name
        self.price = price
        self.quantity = quantity

    def get_total_value(self) -> float:
        """Calculate the total value of this product's stock.
        
        Returns:
            The total value (price * quantity)
        """
        return self.price * self.quantity

    def update_quantity(self, amount: int) -> None:
        """Update the product quantity by the given amount.
        
        Args:
            amount: The amount to add (negative to subtract)
        """
        self.quantity = max(self.quantity + amount, 0)


class Inventory:
    """Manages a collection of products and their stock levels.
    
    Attributes:
        products (Dict[str, Product]): Dictionary mapping product names to Product objects
    """
    
    def __init__(self) -> None:
        """Initialize an empty inventory."""
        self.products: Dict[str, Product] = {}

    def add_product(self, product: Product) -> None:
        """Add a product to the inventory.
        
        Args:
            product: The Product object to add
        """
        self.products[product.name] = product

    def remove_product(self, name: str) -> bool:
        """Remove a product from the inventory.
        
        Args:
            name: The name of the product to remove
            
        Returns:
            True if product was removed, False if product not found
        """
        try:
            del self.products[name]
            return True
        except KeyError:
            return False

    def get_product(self, name: str) -> Optional[Product]:
        """Get a product by name.
        
        Args:
            name: The name of the product to retrieve
            
        Returns:
            The Product object if found, None otherwise
        """
        return self.products.get(name)

    def calculate_total_inventory_value(self) -> float:
        """Calculate the total value of all products in inventory.
        
        Returns:
            The total inventory value
        """
        total = 0
        for name, product in self.products.items():
            total += product.get_total_value()
        return total

    def find_low_stock(self, threshold: int) -> List[str]:
        """Find products with stock below the given threshold.
        
        Args:
            threshold: The minimum stock level
            
        Returns:
            List of product names with low stock
        """
        low_stock = []
        for name, product in self.products.items():
            if product.quantity < threshold:
                low_stock.append(name)
        return low_stock

    def apply_discount(self, name: str, percent: float) -> bool:
        """Apply a percentage discount to a product's price.
        
        Args:
            name: The name of the product
            percent: The discount percentage (0-100)
            
        Returns:
            True if discount was applied, False if product not found
        """
        product = self.get_product(name)
        if product is not None:
            product.price = product.price - (product.price * percent / 100)
            return True
        return False

    def restock(self, name: str, amount: int) -> bool:
        """Add stock to a product.
        
        Args:
            name: The name of the product
            amount: The amount to add to stock
            
        Returns:
            True if restock was successful, False if product not found
        """
        product = self.get_product(name)
        if product is not None:
            product.update_quantity(amount)
            return True
        return False

    def export_to_json(self, filename: str) -> None:
        """Export inventory data to a JSON file.
        
        Args:
            filename: The path to the output JSON file
        """
        data = {}
        for name, product in self.products.items():
            data[name] = {"price": product.price, "quantity": product.quantity}
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def import_from_json(self, filename: str) -> None:
        """Import inventory data from a JSON file.
        
        Args:
            filename: The path to the input JSON file
        """
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for name, product_data in data.items():
            self.add_product(Product(name, product_data["price"], product_data["quantity"]))


def process_order(inventory: Inventory, order_items: List[Dict[str, any]]) -> float:
    """Process a customer order and update inventory.
    
    Args:
        inventory: The Inventory object to process against
        order_items: List of dictionaries with 'name' and 'quantity' keys
        
    Returns:
        The total order value
    """
    total = 0
    for item in order_items:
        name = item["name"]
        qty = item["quantity"]
        product = inventory.get_product(name)
        
        if product is None:
            print(f"Product '{name}' not found")
            continue
            
        if product.quantity >= qty:
            product.update_quantity(-qty)
            total += product.price * qty
        else:
            print(f"Not enough stock for {name}")
    return total


if __name__ == "__main__":
    inv = Inventory()
    inv.add_product(Product("Laptop", 999.99, 10))
    inv.add_product(Product("Mouse", 29.99, 50))
    inv.add_product(Product("Keyboard", 79.99, 30))
    print("Total inventory value:", inv.calculate_total_inventory_value())
    print("Low stock items:", inv.find_low_stock(20))