import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
import datetime

from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"

class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    orders = relationship("Purchase", back_populates="client_rel")

    def __repr__(self):
        return f"<Client(id='{self.id}', name='{self.name}', email='{self.email}')>"

class Size(Base):
    __tablename__ = "sizes"

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, unique=True)
    long_name = Column(String(35), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    products = relationship("Product", back_populates="size")
    purchase_items = relationship("PurchaseItem", back_populates="size_rel")

    def __repr__(self):
        return f"<Size(id={self.id}, name='{self.name}')>"

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class Gender(Base):
    __tablename__ = "genders"

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, unique=True)
    long_name = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    products = relationship("Product", back_populates="gender")

    def __repr__(self):
        return f"<Gender(id={self.id}, name='{self.name}')>"

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    inventory = Column(Integer, nullable=False)
    size_id = Column(Integer, ForeignKey('sizes.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    gender_id = Column(Integer, ForeignKey('genders.id'), nullable=False)
    size = relationship("Size", back_populates="products")
    category = relationship("Category", back_populates="products")
    gender = relationship("Gender", back_populates="products")
    images = relationship("ProductImage", back_populates="product")
    order_items = relationship("PurchaseItem", back_populates="product_rel")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Product(id='{self.id}', name='{self.name}', price={self.price}, inventory={self.inventory})>"

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(String(255), nullable=True)
    is_main = Column(Boolean, default=False, nullable=False)
    product = relationship("Product", back_populates="images")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    def __repr__(self):
        return f"<ProductImage(id='{self.id}', product_id='{self.product_id}', url='{self.url[:30]}...')>"

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    client_rel = relationship("Client", back_populates="orders")
    items = relationship("PurchaseItem", back_populates="purchase_rel", cascade="all, delete-orphan", lazy='dynamic')

    def __repr__(self):
        return f"<Purchase(id='{self.id}', client_id='{self.client_id}', status='{self.status}', subtotal={self.subtotal})>"

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    purchase_id = Column(UUID(as_uuid=True), ForeignKey('purchases.id'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    size_id = Column(Integer, ForeignKey('sizes.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_at_purchase = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    purchase_rel = relationship("Purchase", back_populates="items")
    product_rel = relationship("Product", back_populates="order_items")
    size_rel = relationship("Size", back_populates="purchase_items") 