'''
BROKEN RESTAURANT MANAGEMENT SYSTEM
-----------------------------------
This Flask application is intentionally broken with various bugs for students to fix.
Bugs include:
- Route inconsistencies
- Logic errors in calculations
- Missing functionality
- Incorrect data handling
- Template rendering issues
'''

from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)
# load sec key assuing session security
load_dotenv()
app.secret_key = os.getenv("SEC_KEY") 

# Global variables to store data (instead of a database)
MENU_FILE = 'menu.json'
ORDERS_FILE = 'orders.json'

# Initialize data storage
def initialize_data():
    # Bug: This function doesn't check if files exist before loading 
    # (ISAAC: this handles files not existing already just fine. 
    # An improvment could be checking JSON validity to be as expexted, 
    # if not use default. But ill keep this as it is for now) 
    try:
        with open(MENU_FILE, 'r') as f:
            menu = json.load(f)
    except FileNotFoundError:
        # Default menu if file doesn't exist
        menu = {
            'appetizers': [
                {'id': 1, 'name': 'Garlic Bread', 'price': 4.99, 'category': 'appetizers'},
                {'id': 2, 'name': 'Soup of the Day', 'price': 5.99, 'category': 'appetizers'}
            ],
            'main_courses': [
                {'id': 3, 'name': 'Spaghetti Bolognese', 'price': 12.99, 'category': 'main_courses'},
                {'id': 4, 'name': 'Grilled Chicken', 'price': 14.99, 'category': 'main_courses'}
            ],
            'desserts': [
                {'id': 5, 'name': 'Chocolate Cake', 'price': 6.99, 'category': 'desserts'},
                {'id': 6, 'name': 'Ice Cream', 'price': 4.99, 'category': 'desserts'}
            ],
            'drinks': [
                {'id': 7, 'name': 'Soda', 'price': 2.99, 'category': 'drinks'},
                {'id': 8, 'name': 'Coffee', 'price': 3.49, 'category': 'drinks'}
            ]
        }
        with open(MENU_FILE, 'w') as f:
            json.dump(menu, f)
    
    try:
        with open(ORDERS_FILE, 'r') as f:
            orders = json.load(f)
    except FileNotFoundError:
        # Default empty orders if file doesn't exist
        orders = []
        with open(ORDERS_FILE, 'w') as f:
            json.dump(orders, f)
    
    return menu, orders

# Load initial data
menu, orders = initialize_data()

# Save data to file + reload 
def save_data(data_type, data):
    if data_type == 'menu':
        with open(MENU_FILE, 'w') as f:
            json.dump(data, f)
    elif data_type == 'orders':
        with open(ORDERS_FILE, 'w') as f:
            json.dump(data, f)

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Menu routes
@app.route('/menu')
def view_menu():
    # alittle ducktapy, but mets need for now
    menu = initialize_data()[0]
    return render_template('menu.html', menu=menu)

@app.route('/menu/add', methods=['GET', 'POST'])
def add_menu_item():
    name_max: int = 80

    if request.method == 'POST':
        
        category = request.form.get('category')
        if not category:
            flash(f"Category cannot be black, options are: {menu.keys()}")
            return redirect(url_for("add_menu_item"))

        if category not in menu.keys():
            flash(f"{category} does not exist, options are: {menu.keys()}")
            return redirect(url_for("add_menu_item"))

        name = request.form.get('name')
        if not name:
            flash(f"Name cannot be blank")
            return redirect(url_for("add_menu_item"))

        elif len(name) > name_max:
            flash(f"{name} is to long, max is: {name_max}")
            return redirect(url_for("add_menu_item"))

        price = float(request.form.get('price', -1, float)) 
        if price < 0:
            flash("Price must be a number, and must be positve")
            return redirect(url_for("add_menu_item"))
                
        new_id = create_new_id()
        
        menu[category].append({
            'id': new_id,
            'name': name,
            'price': price,
            'category': category
        })
        
        save_data('menu', menu)
        
        return redirect(url_for('view_menu'))
    
    return render_template('add_menu_item.html')

@app.route('/menu/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id: int):
    # Find the item
    item: dict | None = None
    item_index: int
    category = None
    
    # In this case, a small group of items such as items that could apear on menu,
    # a simple linear search is completely fine/ the most appropriate, but for the
    # sake of the request ill implement a linear-binary search hybrid
    
    for cat in menu:
        if menu[cat][0]['id'] <= item_id and menu[cat][-1]['id'] <= item_id:
            category = cat
            item_index = binary_search(item_id, menu[cat],'id')

            if item_index != -1:
                item = menu[cat][item_index]

    if item is None:
        flash('Item not found')
        return redirect(url_for('view_menu'))
    
    if request.method == 'POST':
        name_max: int = 80

        name: str = request.form.get('name', "", str)
        if not name:
            flash(f"Name cannot be blank")
            return redirect(url_for("edit_menu_item", item_id = item_id))

        elif len(name) > name_max:
            flash(f"{name} is to long, max is: {name_max}")
            return redirect(url_for("edit_menu_item", item_id = item_id))

        price: float = request.form.get('price', -1, float)
        if price < 0:
            flash("Price must be a number, and must be positve")
            return redirect(url_for("edit_menu_item", item_id = item_id))
    
        item['name'] = name
        item['price'] = price
        
        save_data('menu', menu)
        
        return redirect(url_for('view_menu'))
    
    return render_template('edit_menu_item.html', item=item)


@app.route('/menu/delete/<int:item_id>')
def delete_menu_item(item_id):
    # Find and remove the item
    for cat in menu:
        if menu[cat][0]['id'] <= item_id and menu[cat][-1]['id'] <= item_id:           
            item_index = binary_search(item_id, menu[cat], 'id')
            menu[cat].pop(item_index)
            save_data('menu', menu)
            return redirect(url_for('view_menu'))
    
    flash('Item not found')
    return redirect(url_for('view_menu'))

# Order routes
@app.route('/orders')
def view_orders():
    orders = initialize_data()[1]
    return render_template('orders.html', orders=orders)

@app.route('/order/new', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        table_number = request.form.get('table_number', -1, int)
        if table_number < 1:
            flash(f"Table number cannot be less then 1")
            redirect(url_for("new_order"))
        
        # Create new order
        new_order = {
            'id': len(orders) + 1,
            'table_number': table_number,
            'items': [],
            'status': 'open',
            'timestamp': str(datetime.now().strftime("%d-%m-%y %H:%M")),
            'total': 0
        }
        
        orders.append(new_order)
        save_data('orders', orders)
        
        return redirect(url_for('view_order', order_id = new_order['id']))
    
    return render_template('new_order.html')

@app.route('/order/<int:order_id>')
def view_order(order_id):
    # Find the order
    order = None
    for o in orders:
        if o['id'] == order_id:
            order = o
            break
    
    if order is None:
        flash('Order not found')
        return redirect(url_for('view_orders'))
    
    return render_template('view_order.html', order=order, menu=menu)

@app.route('/order/<int:order_id>/add_item', methods=['POST'])
def add_item_to_order(order_id):
    # Bug: Missing checking if order exists
    item_id = int(request.form.get('item_id'))
    quantity = int(request.form.get('quantity', 1))
    
    # Find the order
    order = None
    for o in orders:
        if o['id'] == order_id:
            order = o
            break
    
    if order is None:
        flash('Order not found')
        return redirect(url_for('view_orders'))
    
    # Find the menu item
    item = None
    for cat in menu:
        for i in menu[cat]:
            if i['id'] == item_id:
                item = i
                break
    
    if item is None:
        flash('Menu item not found')
        return redirect(url_for('view_order', order_id=order_id))
    
    # Add item to order
    # Bug: Doesn't check if item already exists in order to update quantity
    order['items'].append({
        'id': item['id'],
        'name': item['name'],
        'price': item['price'],
        'quantity': quantity,
        # Bug: Incorrect calculation
        'subtotal': item['price'] * quantity
    })
    
    # Bug: Doesn't update order total
    # order['total'] += item['price'] * quantity
    
    # Bug: Doesn't save updated orders to file
    # save_data('orders', orders)
    
    return redirect(url_for('view_order', order_id=order_id))

@app.route('/order/<int:order_id>/remove_item/<int:item_index>')
def remove_item_from_order(order_id, item_index):
    # Find the order
    order = None
    for o in orders:
        if o['id'] == order_id:
            order = o
            break
    
    if order is None:
        flash('Order not found')
        return redirect(url_for('view_orders'))
    
    subtotal = order['items'][item_index]['subtotal']
    order['total'] -= subtotal
    
    # Remove item
    order['items'].pop(item_index)

    save_data('orders', orders)
    
    return redirect(url_for('view_order', order_id=order_id))

@app.route('/order/<int:order_id>/close')
def close_order(order_id):
    # Find the order
    order = None
    for o in orders:
        if o['id'] == order_id:
            order = o
            break
    
    if order is None:
        flash('Order not found')
        return redirect(url_for('view_orders'))
    
    # Bug: Doesn't recalculate total before closing
    order['status'] = 'closed'
    
    save_data('orders', orders)
    
    return redirect(url_for('view_bill', order_id=order_id))

@app.route('/order/<int:order_id>/bill')
def view_bill(order_id):
    # Find the order
    order = None
    for o in orders:
        if o['id'] == order_id:
            order = o
            break
    
    if order is None:
        flash('Order not found')
        return redirect(url_for('view_orders'))
    
    # Bug: Total calculation is missing or incorrect
    # Calculate total (bug: should be done when adding/removing items)
    total = 0
    for item in order['items']:
        # Bug: Doesn't check if keys exist
        total += item['price'] * item['quantity']
    
    # Bug: Doesn't update order total
    # order['total'] = total
    
    # Bug: Tax calculation is incorrect
    tax = total * 0.1  # 10% tax
    
    return render_template('bill.html', order=order, tax=tax, total=total)

def binary_search(target_value: int, data: list, target_key) -> int:
    low = 0
    high = len(data) - 1

    while low <= high:
        mid = (low + high) // 2
    
        if data[mid][target_key] == target_value:
            return mid
        elif data[mid][target_key] > target_value:
            high = mid -1
        else:
            low = mid + 1
    return -1

def create_new_id():
    new_id: int = 0
    
    for cat in menu:
        for e in menu[cat]:
            if e['id'] > new_id:
                new_id = e['id']

    return new_id
 


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
