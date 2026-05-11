CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    price NUMERIC,
    image TEXT,
    category TEXT
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
);

INSERT INTO products (name, description, price, image, category)
VALUES
('Rain Jacket', 'Waterproof jacket', 120, 'https://images.pexels.com/photos/32328363/pexels-photo-32328363.jpeg', 'men'),
('Fleece Pullover', 'Warm fleece', 80, 'https://images.pexels.com/photos/32328363/pexels-photo-32328363.jpeg', 'men'),
('Trail Pants', 'Durable pants', 90, 'https://images.pexels.com/photos/32328363/pexels-photo-32328363.jpeg', 'men'),
('Waterproof Boots', 'Outdoor boots', 150, 'https://images.pexels.com/photos/32328363/pexels-photo-32328363.jpeg', 'men'),
('Base Layer Shirt', 'Thermal base layer', 60, 'https://images.pexels.com/photos/32328363/pexels-photo-32328363.jpeg', 'men'),
('Beanie Hat', 'Warm beanie', 25, 'https://images.pexels.com/photos/32328363/pexels-photo-32328363.jpeg', 'men'),

('Rain Jacket', 'Women waterproof jacket', 130, 'https://images.pexels.com/photos/15945313/pexels-photo-15945313.jpeg', 'women'),
('Hiking Leggings', 'Comfort leggings', 70, 'https://images.pexels.com/photos/15945313/pexels-photo-15945313.jpeg', 'women'),
('Softshell Jacket', 'Light jacket', 120, 'https://images.pexels.com/photos/15945313/pexels-photo-15945313.jpeg', 'women'),
('Thermal Gloves', 'Warm gloves', 35, 'https://images.pexels.com/photos/15945313/pexels-photo-15945313.jpeg', 'women'),
('Sun Hat', 'Outdoor hat', 28, 'https://images.pexels.com/photos/15945313/pexels-photo-15945313.jpeg', 'women'),

('Kids Raincoat', 'Kids waterproof coat', 60, 'https://images.pexels.com/photos/5792939/pexels-photo-5792939.jpeg', 'kids'),
('Kids Fleece Jacket', 'Kids fleece', 50, 'https://images.pexels.com/photos/5792939/pexels-photo-5792939.jpeg', 'kids'),
('Kids Hiking Boots', 'Kids boots', 70, 'https://images.pexels.com/photos/5792939/pexels-photo-5792939.jpeg', 'kids'),
('Kids Base Layer', 'Kids thermal', 30, 'https://images.pexels.com/photos/5792939/pexels-photo-5792939.jpeg', 'kids'),
('Kids Beanie', 'Kids hat', 20, 'https://images.pexels.com/photos/5792939/pexels-photo-5792939.jpeg', 'kids'),
('Kids Gloves', 'Kids gloves', 18, 'https://images.pexels.com/photos/5792939/pexels-photo-5792939.jpeg', 'kids'),

('Pet Travel Carrier Backpack', 'Pet carrier', 55, 'https://via.placeholder.com/300', 'pets'),
('Portable Folding Dog Crate', 'Dog crate', 85, 'https://via.placeholder.com/300', 'pets'),
('Leak-Proof Pet Travel Water Bottle', 'Pet bottle', 18, 'https://via.placeholder.com/300', 'pets'),
('Pet Travel Food Container Set', 'Food container', 22, 'https://via.placeholder.com/300', 'pets'),
('Car Seat Cover for Pets', 'Seat cover', 30, 'https://via.placeholder.com/300', 'pets'),
('Portable Pet Travel Bed', 'Pet bed', 40, 'https://via.placeholder.com/300', 'pets'),

('Backpack', 'Travel backpack', 90, 'https://via.placeholder.com/300', 'accessories'),
('Hiking Poles', 'Poles', 45, 'https://via.placeholder.com/300', 'accessories'),
('Water Bottle', 'Bottle', 20, 'https://via.placeholder.com/300', 'accessories'),
('Camping Lantern', 'Lantern', 55, 'https://via.placeholder.com/300', 'accessories'),
('Multi-tool', 'Tool', 35, 'https://via.placeholder.com/300', 'accessories'),
('Hiking Hat', 'Hat', 25, 'https://via.placeholder.com/300', 'accessories');

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_email TEXT,
    items TEXT,
    total NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wishlist (
    id SERIAL PRIMARY KEY,
    user_email TEXT,
    product_id INT REFERENCES products(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cart (
    id SERIAL PRIMARY KEY,
    user_email TEXT,
    product_id INT REFERENCES products(id),
    quantity INT DEFAULT 1
);

ALTER TABLE wishlist
ADD CONSTRAINT unique_user_product UNIQUE (user_email, product_id);

ALTER TABLE cart
ADD CONSTRAINT unique_cart_item UNIQUE (user_email, product_id);

SELECT * FROM products;

CREATE DATABASE "Ecommerce";

SELECT current_database();

DELETE FROM cart
WHERE id NOT IN (
    SELECT MIN(id)
    FROM cart
    GROUP BY user_email, product_id
);

ALTER TABLE cart
ADD CONSTRAINT unique_cart_item UNIQUE (user_email, product_id);

SELECT * FROM users;

SELECT * FROM products;

ALTER TABLE cart
ADD COLUMN user_email TEXT;

SELECT * FROM cart;

ALTER TABLE cart
ADD COLUMN product_id INT;

ALTER TABLE cart
ADD CONSTRAINT cart_product_fk
FOREIGN KEY (product_id) REFERENCES products(id);

DROP TABLE cart;

CREATE TABLE cart (
    id SERIAL PRIMARY KEY,
    user_email TEXT,
    product_id INT REFERENCES products(id),
    quantity INT DEFAULT 1
);

SELECT * FROM products;

SELECT * FROM users;

SELECT * FROM cart;

SELECT * FROM orders;

SELECT * FROM wishlist;
